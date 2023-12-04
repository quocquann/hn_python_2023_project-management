

def is_in_group(user):
    return user.groups.filter(name__in=['Stage_Owner', 'PM']).exists()
