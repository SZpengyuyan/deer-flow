# 🧪 AI Test Platform - 测试报告

**生成时间**: 2026-03-24 14:58:46
**测试耗时**: 0.06s

## 📊 执行摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | 32 |
| ✅ 通过 | 32 |
| ❌ 失败 | 0 |
| ⚠️ 错误 | 0 |
| ⏭️ 跳过 | 0 |
| 通过率 | 100.0% |

## 📈 代码覆盖率

**总体覆盖率: 100.0%**

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| sample_code.py | 34 | 0 | 100.0% |

## 📋 测试用例列表

| 测试名称 | 状态 | 耗时 |
|----------|------|------|
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_parametrized[100.0-0.2-80.0] | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_parametrized[200.0-0.5-100.0] | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_parametrized[0.0-0.0-0.0] | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_price_boundary | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_discount_rate_boundary | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_price_none | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_price_wrong_type | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_raises_valueerror | ✅ passed | 0.000s |
| test_sample_code.py::TestCalculateDiscount::test_calculate_discount_raises_valueerror_2 | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_parametrized[1-1] | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_parametrized[3-Fizz] | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_parametrized[5-Buzz] | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_parametrized[15-FizzBuzz] | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_parametrized[7-7] | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_n_boundary | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_n_none | ✅ passed | 0.000s |
| test_sample_code.py::TestFizzbuzz::test_fizzbuzz_n_wrong_type | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_case1 | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_case2 | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_a_boundary | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_b_boundary | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_a_none | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_a_wrong_type | ✅ passed | 0.000s |
| test_sample_code.py::TestSafeDivide::test_safe_divide_raises_zerodivisionerror | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_init | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_init_defaults | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_add_item | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_add_item_raises_valueerror_1 | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_add_item_raises_valueerror_2 | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_total | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_item_count | ✅ passed | 0.000s |
| test_sample_code.py::TestShoppingCart::test_clear | ✅ passed | 0.000s |

## � 原始输出

```
============================= test session starts =============================
collected 32 items

test_sample_code.py ................................                     [100%]

--------------------------------- JSON report ---------------------------------
report saved to: d:\deer-flow\test-playground\tests\.test_report.json
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.13-final-0 _______________

Name                                                 Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------
D:\deer-flow\test-playground\source\sample_code.py      34      0   100%
----------------------------------------------------------------------------------
TOTAL                                                   34      0   100%
Coverage JSON written to file coverage.json
============================= 32 passed in 0.06s ==============================

```