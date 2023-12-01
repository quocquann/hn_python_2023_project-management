def check_token(user, token):
    return user.customuser.verify_token == token
