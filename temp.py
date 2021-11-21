def AddUserButtonClicked(self):
    userLogin = self.Login.text()
    userPassword = self.Password.text()
    if self.UserRole.text() == "Оператор":
        userRole = "Oper"
    elif self.UserRole.text() == "Администратор":
        userRole = "Admin"
    elif self.UserRole.text() == "Разработчик модели":
        userRole = "Develop"