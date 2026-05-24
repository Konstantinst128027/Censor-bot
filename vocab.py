from typing import List

class Vocab:
    def __init__(self, token_lists: List[List[str]]) -> None:
        self.itos = ["<PAD>", "<UNK>"] # специальные символы: pad - пробел, unk - неизвестное слово
        self.stoi = {}

        freq = {}

        # Считаем частоты токенов
        for tokens in token_lists:
            for token in tokens:
                freq[token] = freq.get(token, 0) + 1

        # Добавляем токены, которые встретились хотя бы 1 раз
        for token, _ in freq.items():
            if token not in self.itos:
                self.itos.append(token)

        self.stoi = {token: i for i, token in enumerate(self.itos)}

        self.pad_id = self.stoi["<PAD>"]
        self.unk_id = self.stoi["<UNK>"]

    def encode(self, tokens: List[str]) -> List[int]:
        return [self.stoi.get(t, self.unk_id) for t in tokens]

    def __len__(self) -> int:
        return len(self.itos)



def tokenize(text: str) -> List[str]:
    return text.split()
