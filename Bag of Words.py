import numpy as np
import torch
import torch.nn as nn
import torchtext
import copy
from datetime import datetime
from sklearn.metrics import confusion_matrix
import pyperclip
from datasets import load_dataset
from models import BoW

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
#https://huggingface.co/datasets/s-nlp/en_non_detoxified/viewer/s-nlp--en_non_detoxified
#Load the data

train_dataset_dict = load_dataset('json', data_files='data/train_random.single.json')
valid_data = load_dataset('json', data_files='data/test_random.single.json',split='train[:50%]')
test_data = load_dataset('json', data_files='data/test_random.single.json',split='train[50%:]')
test_data2 = copy.deepcopy(test_data)
train_data = train_dataset_dict['train']

# prepare the data

tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
max_length = 600

##
# The following function tokenizes the test string only.
# This function and the following three lines were commented out for testing tokenization with lemmatization.
##
def tokenize_example(example, tokenizer, max_length):
    tokens = tokenizer(example['text'])[:max_length]
    return {'tokens': tokens}

train_data = train_data.map(tokenize_example, fn_kwargs={'tokenizer': tokenizer, 'max_length': max_length})
valid_data = valid_data.map(tokenize_example, fn_kwargs={'tokenizer': tokenizer, 'max_length': max_length})
test_data = test_data.map(tokenize_example, fn_kwargs={'tokenizer': tokenizer, 'max_length': max_length})

##
# The following code (including the three lines after the function) were commented out for testing tokenization without lemmatization.
##
# lemmatizer = WordNetLemmatizer()
# tokenizer = nltk.RegexpTokenizer(r"\w+")
#
# def tokenize_lemmatize_column(record, tokenizer, lemmatizer, max_length):
#     # make it lower case
#     input_str = record['text']
#     input_str = input_str.lower()
#
#     # tokenizer.tokenize strips out the unwanted characters and splits on space
#     tokens = tokenizer.tokenize(input_str)
#     tokens = tokens[:max_length]
#
#     lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
#     return {'tokens': lemmatized_tokens}
#
# train_data = train_data.map(tokenize_lemmatize_column, fn_kwargs={'tokenizer': tokenizer, 'lemmatizer': lemmatizer, 'max_length': max_length})
# valid_data = valid_data.map(tokenize_lemmatize_column, fn_kwargs={'tokenizer': tokenizer, 'lemmatizer': lemmatizer, 'max_length': max_length})
# test_data = test_data.map(tokenize_lemmatize_column, fn_kwargs={'tokenizer': tokenizer, 'lemmatizer': lemmatizer, 'max_length': max_length})



# build a vocabulary

vocab = torchtext.vocab.build_vocab_from_iterator(train_data['tokens'],
                                                  min_freq=5,
                                                  specials=['<unk>', '<pad>'])
vocab.set_default_index(vocab['<unk>'])
# Numericalize `train_data`, `valid_data`, and `test_data` by indexing all tokens according to the vocabulary:

def numericalize_data(example, vocab):
    ids = [vocab[token] for token in example['tokens']]
    return {'ids': ids}

train_data = train_data.map(numericalize_data, fn_kwargs={'vocab': vocab})
valid_data = valid_data.map(numericalize_data, fn_kwargs={'vocab': vocab})
##
# The following line was commented until the final model was trained and the results with the test data were evaluated.
##
test_data = test_data.map(numericalize_data, fn_kwargs={'vocab': vocab})

# The updated dataset now contains `ids`:
# Finally, we create a binary encoding of each example as a multi-hot vector for our Bag-of-words model

def multi_hot_data(example, num_classes):
    encoded = np.zeros((num_classes,))
    encoded[example['ids']] = 1
    return {'multi_hot': encoded}

train_data = train_data.map(multi_hot_data, fn_kwargs={'num_classes': len(vocab)})
valid_data = valid_data.map(multi_hot_data, fn_kwargs={'num_classes': len(vocab)})
##
# The following line was commented until the final model was trained and the results with the test data were evaluated.
##
test_data = test_data.map(multi_hot_data, fn_kwargs={'num_classes': len(vocab)})

# Convert the dataset to `torch` types, only keeping `multi-hot` and `label`:

train_data = train_data.with_format(type='torch', columns=['multi_hot', 'label'])
valid_data = valid_data.with_format(type='torch', columns=['multi_hot', 'label'])
##
# The following line was commented until the final model was trained and the results with the test data were evaluated.
##
test_data = test_data.with_format(type='torch', columns=['multi_hot', 'label'])

# Wrap each in a `torch.utils.data.DataLoader` with a given batch size and shuffling for the training data:

train_dataloader = torch.utils.data.DataLoader(train_data, batch_size=128, shuffle=True)
valid_dataloader = torch.utils.data.DataLoader(valid_data, batch_size=128)
##
# The following two lines were commented until the final model was trained and the results with the test data were evaluated.
##
test_dataloader = torch.utils.data.DataLoader(test_data, batch_size=128)
test_dataloader2 = torch.utils.data.DataLoader(test_data, batch_size=1)

## Bag-of-words model
#
# Implement a simple neural net with one or two hidden layers which takes inputs of `vocab_size` and has 'num_neuronsX` units in each hidden layer.
# The output layer has `6` units - mapping to our six classes,
# arts_&_culture (0), business_&_entrepreneurs (1), pop_culture (2), daily_life (3), sports_&_gaming (4), and science_&_technology (5).

# Instantiate the Model
model = BoW(vocab_size=len(vocab)).to(device)

# Define the optimiser and tell it what parameters to update, as well as the loss function
# The following assignments were adjusted during tuning
learning_rate = 0.002
num_epochs = 9

optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
loss_fn = nn.CrossEntropyLoss().to(device)

# Define function `train`, which trains our model for one epoch and returns the mean training loss.

def train(model, dataloader, loss_fn, optimizer, device):
    model.train()
    losses, accuracies = [], []
    for batch in dataloader:
        inputs = batch['multi_hot'].to(device)
        labels = batch['label'].to(device)
        # Reset the gradients for all variables
        optimizer.zero_grad()
        # Forward pass
        preds = model(inputs)
        # Calculate loss
        loss = loss_fn(preds, labels)
        # Backward pass
        loss.backward()
        # Adjust weights
        optimizer.step()
        # Log
        losses.append(loss.detach().cpu().numpy())
        accuracy = torch.sum(torch.argmax(preds, dim=-1) == labels) / labels.shape[0]
        accuracies.append(accuracy.detach().cpu().numpy())
    return np.mean(losses), np.mean(accuracies)

# Define function `evaluate`, which we will use to evaluate the model with the validation and test sets.

def evaluate(model, dataloader, loss_fn, device):
    model.eval()
    losses, accuracies = [], []
    all_labels, all_preds = [], []  # Added variables to store labels and predictions

    with torch.no_grad():
        for batch in dataloader:
            inputs = batch['multi_hot'].to(device)
            labels = batch['label'].to(device)
            # Forward pass
            preds = model(inputs)
            # Calculate loss
            loss = loss_fn(preds, labels)
            # Log
            losses.append(loss.detach().cpu().numpy())

            # Store labels and predictions
            all_labels.extend(labels.detach().cpu().numpy())
            all_preds.extend(torch.argmax(preds, dim=-1).detach().cpu().numpy())

        accuracy = torch.sum(torch.argmax(preds, dim=-1) == labels) / labels.shape[0]
        accuracies.append(accuracy.detach().cpu().numpy())

    # Calculate confusion matrix
    confusion_mat = confusion_matrix(all_labels, all_preds)

    return np.mean(losses), np.mean(accuracies), confusion_mat

# Train for X epochs:

train_losses, train_accuracies = [], []
valid_losses, valid_accuracies = [], []
##
# The following  line was commented until the final model was trained and the results with the test data were evaluated.
##
test_losses, test_accuracies = [], []
for epoch in range(num_epochs):
    # Train
    train_loss, train_accuracy = train(model, train_dataloader, loss_fn, optimizer, device)
#     # Evaluate
    valid_loss, valid_accuracy, confusion_mat = evaluate(model, valid_dataloader, loss_fn, device)
    ##
    # The following  line was commented until the final model was trained and the results with the test data were evaluated.
    ##
    test_loss, test_accuracy, test_confusion_mat = evaluate(model, test_dataloader, loss_fn, device)

    # Log
    train_losses.append(train_loss)
    train_accuracies.append(train_accuracy)
    valid_losses.append(valid_loss)
    valid_accuracies.append(valid_accuracy)
    ##
    # The following 2 lines were commented until the final model was trained and the results with the test data were evaluated.
    ##
    test_losses.append(test_loss)
    test_accuracies.append(test_accuracy)
    print("Epoch {}: train_loss={:.4f}, train_accuracy={:.4f}, valid_loss={:.4f}, valid_accuracy={:.4f}".format(
        epoch+1, train_loss, train_accuracy, valid_loss, valid_accuracy))

print(confusion_mat)
np.savetxt(datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+"-valid.csv", confusion_mat, delimiter=",")

# Plot loss and accuracy curves for training and validation:

import matplotlib.pyplot as plt
fig, ax1 = plt.subplots(1, 1, figsize=(9.75, 6.5), sharex=True)
fig.suptitle('Epochs: '+str(num_epochs)+"  LR: {:6.4f}".format(learning_rate)+"  Config: "+model.get_config())
ax1.plot(train_losses, color='g', linestyle='dashed', label='train loss')
ax1.plot(valid_losses, color='r', linestyle='dashed', label='valid loss')
ax1.set_ylabel("Loss")
ax1.set_title("Last training loss: {:10.3f}".format(train_loss) + "     Last validation loss: {:10.3f}".format(valid_loss) + "\n" + "Last training accuracy: {:10.3f}".format(train_accuracy) + "     Last validation accuracy: {:10.3f}".format(valid_accuracy))
ax1.plot(train_accuracies, color='m',  linewidth=1.5, label='train accuracy')
ax1.plot(valid_accuracies, color='b',  linewidth=1.5, label='valid accuracy')
ax1.set_ylim([0.,2.])
ax1.legend()
plt.savefig(datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+".png")

# Evaluate the final model on the test set:
##
# The following  line was set to False until the final model was trained and the results with the test data were evaluated.
##
torch.save(model.state_dict(), "model_file")

show_test = True
if show_test:
    # test_losses, test_accuracy, confusion_mat = evaluate(model, test_dataloader, loss_fn, device)
    print("Test loss: {:.3f}".format(test_loss))
    print("Test accuracy: {:.3f}".format(test_accuracy))
    print()
    print('Test dataset length', len(test_dataloader), test_dataloader.dataset.num_rows)
    print('Confusion Matrix:')
    print(confusion_mat)
    np.savetxt(datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+"-test.csv", confusion_mat, delimiter=",")


    fig, ax1 = plt.subplots(1, 1, figsize=(9.75, 6.5), sharex=True)
    fig.suptitle('Epochs: '+str(num_epochs)+"  LR: {:6.4f}".format(learning_rate)+"  Config: BoW-test "+model.get_config())
    ax1.plot(train_losses, color='g', linestyle='dashed', label='train loss')
    ax1.plot(valid_losses, color='r', linestyle='dashed', label='valid loss')
    ax1.plot(test_losses, color='c', linestyle='dashed', label='test loss')
    ax1.set_ylabel("Loss")
    ax1.set_title("Last training loss: {:10.3f}".format(train_loss) + "     Last validation loss: {:10.3f}".format(valid_loss) + "     Last test loss: {:10.3f}".format(test_loss) + "\n" + "Last training accuracy: {:10.3f}".format(train_accuracy) + "     Last validation accuracy: {:10.3f}".format(valid_accuracy) + "     Last test accuracy: {:10.3f}".format(test_accuracy))
    ax1.plot(train_accuracies, color='m',  linewidth=1.5, label='train accuracy')
    ax1.plot(valid_accuracies, color='b',  linewidth=1.5, label='valid accuracy')
    ax1.plot(test_accuracies, color='y',  linewidth=1.5, label='test accuracy')
    ax1.set_ylim([0.,2.])
    ax1.legend()
    plt.savefig(datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+".png")
    pyperclip.copy(float(valid_accuracy))

    # preds = model(inputs)

    # The following code is to look at individual tweets and the prediction for debugging purposes
    exit()
    i = 0
    for batch in test_dataloader2:
        inputs = batch['multi_hot'].to(device)
        labels = batch['label'].to(device)
        preds = model(inputs)
        print(inputs)
        print('Prediction', torch.argmax(preds).item(), preds)
        print('Actual', batch['label'].item())
        print()
        print('Text', test_data2[i]['text'])
        print('label', test_data2[i]['label'])
        print('label_name', test_data2[i]['label_name'])
        input(" ")
        i += 1
