"""
示例源代码 - 用于验证 AI Test Platform 的测试用例生成功能

包含函数和类两种形式的被测代码。
"""


def calculate_discount(price: float, discount_rate: float) -> float:
    """计算折扣后的价格。

    Args:
        price: 原价，必须非负
        discount_rate: 折扣率，范围 [0, 1]

    Returns:
        折扣后的价格

    Raises:
        ValueError: 当 price 为负或 discount_rate 超出范围时
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1")
    return price * (1 - discount_rate)


def fizzbuzz(n: int) -> str:
    """经典 FizzBuzz 函数。

    Args:
        n: 输入整数

    Returns:
        "FizzBuzz", "Fizz", "Buzz" 或数字字符串
    """
    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    return str(n)


def safe_divide(a: float, b: float) -> float:
    """安全除法，处理除零情况。

    Raises:
        ZeroDivisionError: 当 b 为 0 时
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


class ShoppingCart:
    """购物车类。"""

    def __init__(self, owner: str):
        """初始化购物车。

        Args:
            owner: 购物车所有者名称
        """
        self.owner = owner
        self.items: list[dict] = []

    def add_item(self, name: str, price: float, quantity: int = 1) -> None:
        """添加商品到购物车。

        Raises:
            ValueError: 当 price 为负或 quantity 小于 1 时
        """
        if price < 0:
            raise ValueError("Price cannot be negative")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self.items.append({"name": name, "price": price, "quantity": quantity})

    def total(self) -> float:
        """计算购物车总价。"""
        return sum(item["price"] * item["quantity"] for item in self.items)

    def item_count(self) -> int:
        """返回购物车中的商品种类数。"""
        return len(self.items)

    def clear(self) -> None:
        """清空购物车。"""
        self.items = []
