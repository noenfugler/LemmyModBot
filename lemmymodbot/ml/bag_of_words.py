import torch
import torch.nn as nn
import pandas as pd
import torchtext
from sklearn.model_selection import train_test_split
import numpy as np

torch.set_default_dtype(torch.float64)


class BagOfWords(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        # the following two assignment was adjusted during tuning
        self.vocab_size = vocab_size
        self.dropout_rate = 0.1
        self.num_neurons1 = 512
        self.num_neurons2 = 64
        self.hidden1 = nn.Linear(vocab_size, self.num_neurons1)
        self.dropout1 = nn.Dropout(self.dropout_rate)
        if self.num_neurons2 > 0:
            self.hidden2 = nn.Linear(self.num_neurons1, self.num_neurons2)
            self.dropout2 = nn.Dropout(self.dropout_rate)
            self.out = nn.Linear(self.num_neurons2, 2)
        else:
            self.out = nn.Linear(self.num_neurons1, 2)

    def forward(self, x):
        if x.dtype != torch.float64:
            x = x.double()
        x = nn.ReLU()(self.hidden1(x))
        # x = self.dropout1(x)
        if self.num_neurons2 > 0:
            x = nn.ReLU()(self.hidden2(x))
            x = self.dropout2(x)
        x = nn.Sigmoid()(self.out(x))
        return x

    def get_config(self):
        if self.num_neurons2 == 0:
            return str(self.num_neurons1)
        else:
            return str(self.num_neurons1) + "-" + str(self.num_neurons2)


def build_bow_model():
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    from torch.utils.data import Dataset
    torch.set_default_tensor_type(torch.DoubleTensor)

    class MyDataset(Dataset):

        def __init__(self, df):
            # df.reset_index(drop=True, inplace=True)
            x = df.iloc[:, 0].values
            # x = np.float32(x)
            y = df.iloc[:, 1:].values
            y = y.astype(np.float64)
            self.x = x
            self.y = y
            # reasons['not_toxic'] = df.iloc[:, 0].apply[]
            # resons_json = json.loads(reasons)

            # self.x = torch.tensor(x) #), dtype=torch.float32)
            # self.y = torch.tensor(y) #, dtype=torch.float32)

        def __len__(self):
            return len(self.y)

        def __getitem__(self, idx):
            return self.x[idx], self.y[idx]

    # train_dataset_dict = load_dataset('text', data_files='training/train.tsv')

    all_data = pd.read_csv("training/train.tsv", sep='\t', lineterminator='\n')
    # train_data

    tokenizer = torchtext.data.utils.get_tokenizer("basic_english")
    # max_length = 2400
    all_data['tokens'] = all_data.apply(lambda row: tokenizer(row['comment']), axis=1)

    # build a vocabulary

    vocab = torchtext.vocab.build_vocab_from_iterator(all_data['tokens'],
                                                      min_freq=5,
                                                      specials=['<unk>', '<pad>'])
    vocab.set_default_index(vocab['<unk>'])

    # print(len(vocab))

    def numericalize_data(example, vocab):
        ids = [vocab[token] for token in example['tokens']]
        return ids

    # train_data = train_data.map(numericalize_data, fn_kwargs={'vocab': vocab})
    # valid_data = valid_data.map(numericalize_data, fn_kwargs={'vocab': vocab})

    all_data['ids'] = all_data.apply(lambda row: numericalize_data(row, vocab), axis=1)

    # print(all_data)

    def multi_hot_data(example, num_classes):
        encoded = np.zeros((num_classes,))
        encoded[example['ids']] = 1
        pass
        return encoded

    # train_data = train_data.map(multi_hot_data, fn_kwargs={'num_classes': len(vocab)})

    all_data['multi_hot'] = all_data.apply(lambda row: multi_hot_data(row, len(vocab)), axis=1)
    # print(all_data)

    # Extract four labels into their own columns

    all_data['toxic_content'] = all_data.apply(lambda row: '"toxic_content":true' in row['reasons'], axis=1)
    all_data['not_toxic_content'] = all_data.apply(lambda row: '"toxic_content":true' not in row['reasons'], axis=1)
    # all_data['unclear'] = all_data.apply(lambda row: '"unclear":true' in row['reasons'], axis=1)
    # all_data['other_tick'] = all_data.apply(lambda row: '"other_tick":true' in row['reasons'], axis=1)

    # Convert to 1/0 format
    all_data['toxic_content'] = all_data['toxic_content'].astype(int)
    all_data['not_toxic_content'] = all_data['not_toxic_content'].astype(int)
    # all_data['not_toxic'] = all_data['not_toxic'].astype(int)
    # all_data['unclear'] = all_data['unclear'].astype(int)
    # all_data['other_tick'] = all_data['other_tick'].astype(int)

    # split dataset , only keeping `multi-hot` and `label columns`:

    all_data = all_data[['multi_hot', 'toxic_content', 'not_toxic_content']]  # , 'not_toxic', 'unclear', 'other_tick']]
    # all_data
    train_data, valid_data = train_test_split(all_data, test_size=0.1, random_state=2)
    # valid_data, test_data = train_test_split(non_train_data, test_size=0.333, random_state=0)
    # train_data.reset_index(drop=True, inplace=True)
    # valid_data.reset_index(drop=True, inplace=True)
    # test_data.reset_index(drop=True, inplace=True)

    train_dataset = MyDataset(train_data)
    valid_dataset = MyDataset(valid_data)
    # test_dataset = MyDataset(test_data)

    # train_dataset = PandasDataset(train_data)
    # valid_dataset = PandasDataset(valid_data)
    # test_dataset = PandasDataset(test_data)
    # train_dataset = torch.tensor(train_data)
    # valid_dataset = torch.tensor(valid_data)
    # test_dataset = torch.tensor(test_data)
    # tests

    # train_tensor = torch.tensor(train_data)
    # valid_tensor = torch.tensor(valid_data)
    # test_tensor = torch.tensor(test_data)

    train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)
    valid_dataloader = torch.utils.data.DataLoader(valid_dataset, batch_size=128, shuffle=True)
    # test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=128, shuffle=True)
    # train_dataloader

    model = BagOfWords(vocab_size=len(vocab)).to(device)
    model.double()

    # Define the optimiser and tell it what parameters to update, as well as the loss function
    # The following assignments were adjusted during tuning
    learning_rate = 0.001
    num_epochs = 7

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.CrossEntropyLoss().to(device)

    # loss_fn = nn.BCELoss().to(device)
    # loss_fn = nn.MSELoss().to(device)
    # metric = BinaryAccuracy(threshold=0.9)
    # Define function `train`, which trains our model for one epoch and returns the mean training loss.

    def train(model, dataloader, loss_fn, optimizer, device):
        # def train(model, X, y, loss_fn, optimizer, device):

        model.train()
        losses, accuracies = [], []
        # print('bar')
        for batch in dataloader:
            inputs = batch[0].to(device)
            reasons = batch[1].to(device)
            # reasons = torch.transpose(reasons)
            # Reset the gradients for all variables
            optimizer.zero_grad()
            # Forward pass
            preds = model(inputs)
            preds = preds.squeeze()
            # preds = torch.transpose(preds)
            # Calculate loss
            # foo = torch.transpose(preds)
            loss = loss_fn(preds, reasons)
            # Backward pass
            loss.backward()
            # Adjust weights
            optimizer.step()
            # Log
            losses.append(loss.detach().cpu().numpy())
            accuracy = torch.sum(torch.argmax(preds, dim=-1) == torch.argmax(reasons, dim=-1)) / reasons.shape[0]
            # accuracy = torch.sum(torch.argmax(preds) == reasons) / reasons.shape[0]
            # accuracy = torch.sum(torch.sum(((preds>0.5).float() == reasons).float()/4.0,1)) / reasons.shape[0]
            """ The above line calculates accuracy as follows:
            For each of the labels, round the prediction to either 0 or 1
            Divide the predictions by the number of labels (4)
            Sum across rows
            Average across columns."""
            # metric.update(preds, reasons)
            # accuracy = metric.compute()

            accuracies.append(accuracy.detach().cpu().numpy())
        return np.mean(losses), np.mean(accuracies)

    # Define function `evaluate`, which we will use to evaluate the model with the validation and tests sets.

    def evaluate(model, dataloader, loss_fn, device):
        model.eval()
        losses, accuracies = [], []
        all_reasons, all_preds = [], []  # Added variables to store reasons and predictions

        with torch.no_grad():
            for batch in dataloader:
                # inputs = batch['multi_hot'].to(device)
                # reasonss = batch['reasons'].to(device)
                inputs = batch[0].to(device)
                reasons = batch[1].to(device)

                # Forward pass
                preds = model(inputs)
                preds = preds.squeeze()
                # Calculate loss
                loss = loss_fn(preds, reasons)
                # Log
                losses.append(loss.detach().cpu().numpy())

                # Store reasonss and predictions
                all_reasons.extend(reasons.detach().cpu().numpy())
                # all_preds.extend(torch.argmax(preds, dim=-1).detach().cpu().numpy())
                # accuracy = torch.sum(torch.sum(((preds > 0.5).float() == reasons).float() / 4.0, 1)) / reasons.shape[0]
                all_preds.extend((preds > 0.5).float())
                accuracy = torch.sum(torch.argmax(preds, dim=-1) == torch.argmax(reasons, dim=-1)) / reasons.shape[0]
                accuracies.append(accuracy.detach().cpu().numpy())
            # accuracy = torch.sum(torch.argmax(preds, dim=-1) == reasons) / reasons.shape[0]
            # accuracy = torch.sum(torch.sum(((preds>0.5).float() == reasons).float()/4.0,1)) / reasons.shape[0]
            # """ The above line calculates accuracy as follows:
            # For each of the labels, round the prediction to either 0 or 1
            # Divide the predictions by the number of labels (4)
            # Sum across rows
            # Average across columns."""
            # metric.update(preds, reasons)
            # accuracy = metric.compute()

        # Calculate confusion matrix
        # confusion_mat = confusion_matrix(all_reasons, all_preds)

        return np.mean(losses), np.mean(accuracies)

    # Train for X epochs:

    train_losses, train_accuracies = [], []
    valid_losses, valid_accuracies = [], []

    for epoch in range(num_epochs):
        # Train
        train_loss, train_accuracy = train(model, train_dataloader, loss_fn, optimizer, device)
        #     # Evaluate
        #     valid_loss, valid_accuracy, confusion_mat = evaluate(model, valid_dataloader, loss_fn, device)
        valid_loss, valid_accuracy = evaluate(model, valid_dataloader, loss_fn, device)
        ##
        # The following  line was commented until the final model was trained and the results with the tests data were evaluated.
        ##
        # test_loss, test_accuracy, test_confusion_mat = evaluate(model, test_dataloader, loss_fn, device)

        # Log
        train_losses.append(train_loss)
        train_accuracies.append(train_accuracy)
        valid_losses.append(valid_loss)
        valid_accuracies.append(valid_accuracy)
        ##
        # The following 2 lines were commented until the final model was trained and the results with the tests data were evaluated.
        ##
        # test_losses.append(test_loss)
        # test_accuracies.append(test_accuracy)
        print("Epoch {}: train_loss={:.4f}, train_accuracy={:.4f}, valid_loss={:.4f}, valid_accuracy={:.4f}".format(
            epoch + 1, train_loss, train_accuracy, valid_loss, valid_accuracy))

    # import matplotlib.pyplot as plt
    # fig, ax1 = plt.subplots(1, 1, figsize=(9.75, 6.5), sharex=True)
    # fig.suptitle('Epochs: '+str(num_epochs)+"  LR: {:6.4f}".format(learning_rate)+"  Config: "+model.get_config())
    # ax1.plot(train_losses, color='g', linestyle='dashed', label='train loss')
    # ax1.plot(valid_losses, color='r', linestyle='dashed', label='valid loss')
    # ax1.set_ylabel("Loss")
    # ax1.set_title("Last training loss: {:10.3f}".format(train_loss) + "     Last validation loss: {:10.3f}".format(valid_loss) + "\n" + "Last training accuracy: {:10.3f}".format(train_accuracy) + "     Last validation accuracy: {:10.3f}".format(valid_accuracy))
    # ax1.plot(train_accuracies, color='m',  linewidth=1.5, label='train accuracy')
    # ax1.plot(valid_accuracies, color='b',  linewidth=1.5, label='valid accuracy')
    # ax1.set_ylim([0.,2.])
    # ax1.legend()
    # plt.show()
    # plt.savefig(datetime.now().strftime("%Y-%m-%dT%H-%M-%S")+".png")

    torch.save(model.state_dict(), "data/model.mdl")
