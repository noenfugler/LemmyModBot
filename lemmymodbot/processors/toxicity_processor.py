import torch

from lemmymodbot.ml import ToxicityClassifier
from lemmymodbot.processors import Processor, Content, LemmyHandle, ContentResult
from lemmymodbot.processors.base import ContentType


class ToxicityProcessor(Processor):
    classifier: ToxicityClassifier
    uncertainty_allowance = 0.2

    def __init__(self, classifier: ToxicityClassifier = ToxicityClassifier()):
        self.classifier = classifier

    def setup(self) -> None:
        self.classifier.setup()

    def execute(self, content: Content, handle: LemmyHandle) -> ContentResult:
        if content.type == ContentType.POST_LINK:
            return ContentResult.nothing()

        local_flags = []
        preds, preds2, preds3 = self.classifier.classify(content)
        print('\n\n' + content.content)
        print(f'{preds}', (1 - torch.argmax(preds)).item())
        if preds[0].item() < 0.2 and preds[1].item() < 0.2:
            print("Low values^")
        if abs(preds[0].item() - preds[1].item()) < self.uncertainty_allowance:
            print("Close values^")
        if preds2 == 1 and preds3 >= self.uncertainty_allowance:
            print("Toxic^")
            local_flags.append('potentially toxic')

        return ContentResult(local_flags, {
            "toxicity": preds[0].item(),
            "non_toxicity": preds[1].item(),
        })
