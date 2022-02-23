# https://dob-kids.com/2021/03/18/python-tkcalender1/

import tkinter
from tkinter import ttk
from tkcalendar import Calendar, DateEntry

class TestTkcalender(tkinter.Frame):
    def __init__(self,master):
        super().__init__(master)
        self.pack()
        self.master.title("tkカレンダーテスト")
        self.master.geometry("800x600")

        # カレンダーのスタイル
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('my.DateEntry',
                        fieldbackground='light green',
                        background='dark green',
                        foreground='dark orange',
                        arrowcolor='white')

        self.data_entry_date = DateEntry(style='my.DateEntry')
        self.data_entry_date.place(x=250, y=230)

        self.calender_date = Calendar()
        self.calender_date.place(x=500, y=230)

        self.print_button = tkinter.Button(master, text="プリント", bg="coral", font=("Times New Roman", 20), command=self.click_print)
        self.print_button.place(x=400, y=150, width=150, height=50)

    def click_print(self):
        print(self.data_entry_date.get_date())
        print(self.calender_date.get_date())

def main():
    root = tkinter.Tk()
    root = TestTkcalender(master=root)
    root.mainloop()

if __name__ == "__main__":
    main()