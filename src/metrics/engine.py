"""Safe formula evaluator for custom metrics.

Uses a recursive descent parser - NO eval().
Supports: +, -, *, /, parentheses, numbers, and whitelisted variables.
"""

ALLOWED_VARIABLES = {
    "commits", "prs", "issues", "releases", "stars", "forks",
    "deploy_frequency", "lead_time", "mttr", "cfr",
    "contributors", "active_contributors",
}


class FormulaError(Exception):
    pass


def tokenize(formula: str) -> list[str]:
    """Tokenize a formula string into numbers, variables, and operators."""
    tokens = []
    i = 0
    while i < len(formula):
        ch = formula[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "+-*/()":
            tokens.append(ch)
            i += 1
        elif ch.isdigit() or ch == ".":
            # Read number
            j = i
            has_dot = ch == "."
            i += 1
            while i < len(formula) and (formula[i].isdigit() or (formula[i] == "." and not has_dot)):
                if formula[i] == ".":
                    has_dot = True
                i += 1
            tokens.append(formula[j:i])
        elif ch.isalpha() or ch == "_":
            # Read variable name
            j = i
            while i < len(formula) and (formula[i].isalnum() or formula[i] == "_"):
                i += 1
            tokens.append(formula[j:i])
        else:
            raise FormulaError(f"Unexpected character: {ch}")
    return tokens


def _is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def validate_formula(formula: str) -> bool:
    """Validate formula only contains allowed variables and operators."""
    try:
        tokens = tokenize(formula)
    except FormulaError:
        return False
    for token in tokens:
        if token in ALLOWED_VARIABLES:
            continue
        if token in "+-*/()":
            continue
        if _is_number(token):
            continue
        return False
    # Also try parsing to check syntax
    try:
        _Parser(tokens, {v: 0 for v in ALLOWED_VARIABLES}).parse()
    except FormulaError:
        return False
    return True


def evaluate_formula(formula: str, variables: dict[str, float]) -> float:
    """Safely evaluate formula with provided variable values."""
    tokens = tokenize(formula)
    for token in tokens:
        if token in ALLOWED_VARIABLES and token not in variables:
            raise FormulaError(f"Missing variable: {token}")
        if not (_is_number(token) or token in ALLOWED_VARIABLES or token in "+-*/()"):
            raise FormulaError(f"Invalid token: {token}")
    return _Parser(tokens, variables).parse()


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar:
        expr   -> term (('+' | '-') term)*
        term   -> factor (('*' | '/') factor)*
        factor -> NUMBER | VARIABLE | '(' expr ')'
    """

    def __init__(self, tokens: list[str], variables: dict[str, float]):
        self.tokens = tokens
        self.variables = variables
        self.pos = 0

    def parse(self) -> float:
        result = self._expr()
        if self.pos < len(self.tokens):
            raise FormulaError(f"Unexpected token: {self.tokens[self.pos]}")
        return result

    def _peek(self) -> str | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expr(self) -> float:
        result = self._term()
        while self._peek() in ("+", "-"):
            op = self._consume()
            right = self._term()
            if op == "+":
                result += right
            else:
                result -= right
        return result

    def _term(self) -> float:
        result = self._factor()
        while self._peek() in ("*", "/"):
            op = self._consume()
            right = self._factor()
            if op == "*":
                result *= right
            else:
                if right == 0:
                    return 0.0  # Safe division by zero
                result /= right
        return result

    def _factor(self) -> float:
        token = self._peek()
        if token is None:
            raise FormulaError("Unexpected end of formula")

        if token == "(":
            self._consume()
            result = self._expr()
            if self._peek() != ")":
                raise FormulaError("Missing closing parenthesis")
            self._consume()
            return result

        self._consume()
        if _is_number(token):
            return float(token)

        if token in self.variables:
            return self.variables[token]

        if token in ALLOWED_VARIABLES:
            raise FormulaError(f"Missing variable value: {token}")

        raise FormulaError(f"Invalid token: {token}")
