import 'package:bankos_mobile/core/format/money.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('parseAmountToCents', () {
    test('converts an API amount into cents', () {
      expect(parseAmountToCents('898.00'), 89800);
    });

    test('accepts amounts without decimals', () {
      expect(parseAmountToCents('12'), 1200);
    });
  });

  group('parseUserAmountToCents', () {
    test('accepts a comma or a dot as separator', () {
      expect(parseUserAmountToCents('12,5'), 1250);
      expect(parseUserAmountToCents('12.05'), 1205);
    });

    test('returns null for invalid input', () {
      expect(parseUserAmountToCents('abc'), isNull);
      expect(parseUserAmountToCents('1.234'), isNull);
      expect(parseUserAmountToCents(''), isNull);
    });
  });

  group('formatCents', () {
    test('always writes two decimals', () {
      expect(formatCents(5), '0.05');
      expect(formatCents(89800), '898.00');
    });
  });

  group('validateAmountInput', () {
    test('rejects zero and invalid values', () {
      expect(validateAmountInput('0'), isNotNull);
      expect(validateAmountInput('abc'), isNotNull);
    });

    test('accepts a positive amount', () {
      expect(validateAmountInput('25.50'), isNull);
    });
  });
}
