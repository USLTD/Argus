class NavigationManager:
    def __init__(self, sidebar, stack):

        self.sidebar = sidebar
        self.stack = stack

        self.sidebar.currentRowChanged.connect(self.change_page)

    def change_page(self, index):

        self.stack.setCurrentIndex(index)
