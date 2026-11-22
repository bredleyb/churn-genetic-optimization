import { test, expect } from '@playwright/test';
import { clampMonths, displayMonths, replaceMonthDigits } from '../../src/tenure_control.mjs';

test('unidade é parte do mesmo valor textual e acompanha o singular', () => {
  expect(displayMonths(0)).toBe('0 meses');
  expect(displayMonths(1)).toBe('1 mês');
  expect(displayMonths(24)).toBe('24 meses');
  expect(clampMonths(9999)).toBe(999);
  expect(clampMonths(-4)).toBe(0);
});

test('edição atua somente sobre a parte numérica', () => {
  expect(replaceMonthDigits(24, 0, 2, '12')).toBe(12);
  expect(replaceMonthDigits(24, 2, 2, '0')).toBe(240);
  expect(replaceMonthDigits(24, 0, 2, 'abc')).toBe(24);
  expect(replaceMonthDigits(1, 0, 1, '')).toBe(0);
});
