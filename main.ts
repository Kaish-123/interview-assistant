function solution(digits: number[]): number[] {
  const result = [...digits];
  let carry = 1;

  for (let i = result.length - 1; i >= 0 && carry > 0; i--) {
    const sum = result[i] + carry;
    result[i] = sum % 10;
    carry = Math.floor(sum / 10);
  }

  if (carry > 0) {
    result.unshift(1);
  }

  return result;
}
