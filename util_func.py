def create_deadline(id, name, date, priority):
    deadline = {
        "id": id,
        "name": name,
        "date": date,
        "priority": priority,
    }
    return deadline


def return_deadline(deadline):
    res = ''
    res += '\nНазвание: ' + deadline['name'] + '\n'
    res += 'Дата: ' + str(deadline['date']) + '\n'
    res += 'Приоритет: ' + deadline['priority'] + '\n'
    return res