import sys
from collections import defaultdict, deque

class Rule:
    def __init__(self, lhs, rhs, prob):
        self.lhs = lhs
        self.rhs = rhs
        self.prob = prob

class State:
    def __init__(self, lhs, rhs, dot, start, prob=1.0, backptrs=None):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.start = start
        self.prob = prob
        self.backptrs = backptrs or []

    def is_complete(self):
        return self.dot == len(self.rhs)

    def next_symbol(self):
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None

    def advance(self, prob, backptr):
        return State(
            self.lhs,
            self.rhs,
            self.dot + 1,
            self.start,
            self.prob * prob,
            self.backptrs + [backptr]
        )

    def key(self):
        return (self.lhs, tuple(self.rhs), self.dot, self.start)

    def __repr__(self):
        before = " ".join(self.rhs[:self.dot])
        after = " ".join(self.rhs[self.dot:])
        return f"{self.lhs} -> {before} • {after} ({self.start}) [p={self.prob:.6f}]"


def read_grammar(path):
    grammar = defaultdict(list)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            prob = float(parts[0])
            lhs = parts[1]
            rhs = parts[3:]
            grammar[lhs].append(Rule(lhs, rhs, prob))
    return grammar


def read_sentences(path):
    sentences = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                sentences.append(line.split())
    return sentences


def earley_parse(words, grammar, start_symbol="S"):
    n = len(words)
    chart = [dict() for _ in range(n + 1)]

    def add_state(state, i):
        key = state.key()
        if key not in chart[i]:
            chart[i][key] = state
            return True
        else:
            # keep best probability
            if state.prob > chart[i][key].prob:
                chart[i][key] = state
            return False

    # Initialize
    for rule in grammar[start_symbol]:
        add_state(State(rule.lhs, rule.rhs, 0, 0, rule.prob), 0)

    # Main loop
    for i in range(n + 1):
        agenda = deque(chart[i].values())

        while agenda:
            state = agenda.popleft()

            if not state.is_complete():
                next_sym = state.next_symbol()

                # Predictor
                if next_sym in grammar:
                    for rule in grammar[next_sym]:
                        new_state = State(rule.lhs, rule.rhs, 0, i, rule.prob)
                        if add_state(new_state, i):
                            agenda.append(new_state)

                # Scanner
                elif i < n and next_sym == words[i]:
                    new_state = state.advance(1.0, words[i])
                    if add_state(new_state, i + 1):
                        pass

            else:
                # Completer
                for prev in chart[state.start].values():
                    if not prev.is_complete() and prev.next_symbol() == state.lhs:
                        new_state = prev.advance(state.prob, state)
                        if add_state(new_state, i):
                            agenda.append(new_state)

    return chart


def print_chart(chart, words):
    print("Sentence:", " ".join(words))
    print("=" * 60)
    for i, col in enumerate(chart):
        print(f"\nChart[{i}]:")
        for state in col.values():
            print(state)
    print("\n" + "=" * 60 + "\n")


def main():
    if len(sys.argv) != 3:
        print("Usage: python parse.py grammar.gr sentences.sen")
        sys.exit(1)

    grammar_file = sys.argv[1]
    sentence_file = sys.argv[2]

    grammar = read_grammar(grammar_file)
    sentences = read_sentences(sentence_file)

    for words in sentences:
        chart = earley_parse(words, grammar)
        print_chart(chart, words)


if __name__ == "__main__":
    main()