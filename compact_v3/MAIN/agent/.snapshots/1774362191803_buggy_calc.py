def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)  # Bug: crashes on empty list

def process_data(data):
    results = []
    for group in data:
        avg = calculate_average(group)
        results.append(avg)
    return results

# This will crash:
# process_data([[], [1, 2, 3]])
