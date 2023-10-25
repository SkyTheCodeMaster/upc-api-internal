# Validate UPC A code, return boolean

def validate_upca(code: str) -> bool:
  try:
    digits = [int(digit) for digit in list(code)]
  except ValueError:
    return False # If the code isn't entirely integers, it's
                 # obviously not a UPC code.

  if len(digits) != 12:
    return False # UPC-A is 12 digits.
  
  #https://en.wikipedia.org/wiki/Universal_Product_Code#Check_digit_calculation
  check_digit = digits.pop()
  odd_digits = digits[::2]
  even_digits = digits[1::2]

  odd_sum = sum(odd_digits)
  even_sum = sum(even_digits)

  total_sum = (odd_sum*3) + even_sum
  result = total_sum % 10
  if result == 0 and check_digit == 0:
    return True
  elif (10-result) == check_digit:
    return True
  else:
    return False
  
def convert_upce(code: str) -> str:
  try:
    digits = [int(digit) for digit in list(code)]
  except ValueError:
    raise

  if len(digits) != 8:
    raise Exception("Length must be 8!")

  if digits[0] not in [0,1]:
    raise Exception("Invalid start number")

  end_digit = digits[6]

  if (end_digit in [0,1,2]):
    tmpl = "{0}{1}{2}{6}0000{3}{4}{5}{7}".format(*digits)
  elif (end_digit == 3):
    tmpl = "{0}{1}{2}{3}00000{4}{5}{7}".format(*digits)
  elif (end_digit == 4):
    tmpl = "{0}{1}{2}{3}{4}00000{5}{7}".format(*digits)
  elif (end_digit in [5,6,7,8,9]):
    tmpl = "{0}{1}{2}{3}{4}{5}0000{6}{7}".format(*digits)

  if validate_upca(tmpl):
    return tmpl
  else:
    raise Exception("UPC Not Valid")