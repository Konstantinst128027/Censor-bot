import torch


class ToxicCNNBiLSTM(torch.nn.Module):

    def __init__(self,
                 vocab_size: int = 20000,
                 embedding_dim: int = 128,
                 hidden_dim:int = 128,
                 num_filters: int = 100,
                 kernel_size: int = 3,
                 dropout: float = 0.3,
                 padding: int  = 1
                 ) -> None:
        super().__init__()

        self.embedding = torch.nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=padding
        )

        self.cnn = torch.nn.Conv1d(
            in_channels=embedding_dim, # входной размеp одного слова 
            out_channels=num_filters, # количество чисел на выходе для каждой позиции в тексте
            kernel_size=kernel_size, # количество слов в одном окне
            padding=1 # увеличивает справа и слева на один "0", чтобы было легче работать с предложением 
        )

        self.lstm = torch.nn.LSTM(
            input_size=num_filters, # потому что начинает читать по одному слову, сначала первое после втрое и так далее до конца предложения. Поэтому мы передаем читаемы размер как размер одного слова.
            hidden_size=hidden_dim,
            batch_first=True,
            bidirectional=True # получается, что предложение будет проходится с двух сторон
        )

        self.dropout = torch.nn.Dropout(dropout)

        self.fc = torch.nn.Linear(hidden_dim * 2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:

        x = self.embedding(x)
        x = x.permute(0, 2, 1) # меняем размерность как написано в скобках (индекс 0б индекс 2, индекс 1), так нужно для CNN
        x = self.cnn(x)
        x = torch.relu(x) # делает отрицательные значения в нулевые
        x = x.permute(0, 2, 1)

        output, (hidden, cell) = self.lstm(x)
        forward_hidden = hidden[-2] # показывает состояние последнего слова в предложении, то есть все предложение слово по слову оно прошлось и выдало конечный результат для предложения
        backward_hidden = hidden[-1]  # показывает состояние последнего слова в предложении, то есть все предложение слово по слову оно прошлось и выдало конечный результат для предложения (предложение читает в обратную сторону)
        hidden = torch.cat((forward_hidden, backward_hidden),dim=1) # склеиваем два состояния предложения (проходка впрво, проходка влево)
        hidden = self.dropout(hidden) # отключает какое - то количество нейронов, чтобы избежать переобучение
        out = self.fc(hidden)

        return out # [размер батча, 1]
    

def solve_decision(probability: float) -> int:
    if probability > 0.9:
        return 2
    elif 0.85 <= probability <= 0.9:
        return 1
    else:
        return 0