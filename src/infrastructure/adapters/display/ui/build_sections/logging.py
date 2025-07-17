from tkinter.scrolledtext import ScrolledText
import tkinter as tk
from tkinter import ttk

def build_log_section(main_frame):
    logs_frame = ttk.LabelFrame(main_frame, text="Logs", padding=(10, 5))
    logs_frame.grid(row=5, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    logs_frame.rowconfigure(0, weight=1)
    logs_frame.columnconfigure(0, weight=1)
    log_text = ScrolledText(logs_frame, height=4, state='disabled', wrap='word', font=("Consolas", 11))
    log_text.grid(row=0, column=0, sticky='nsew')

    log_text.tag_configure('WORD_INFO', foreground='green', font=('Consolas', 11, 'bold'))
    log_text.tag_configure('WORD_ERR', background='#FFD6D6', foreground='#B20000', font=('Consolas', 11, 'bold'))
    log_text.tag_configure('WORD_WARN', background='#FFFACD', foreground='#B38F00', font=('Consolas', 11, 'bold'))

    def log_message(message, level="INFO", prefix=""):
        log_text['state'] = 'normal'
        # Insere o prefixo normal
        if prefix:
            log_text.insert('end', prefix)

        start = log_text.index('end-1c')
        log_text.insert('end', message)
        end = log_text.index('end-1c')

        if level == "ERROR" or level == "WARNING":
            log_text.tag_add('WORD_ERR', start, end)
        elif level == "INFO":
            log_text.tag_add('WORD_INFO', start, end)
        log_text.insert('end', '\n')
        log_text['state'] = 'disabled'
        log_text.see('end')

    def clear_logs():
        log_text['state'] = 'normal'
        log_text.delete('1.0', 'end')
        log_text['state'] = 'disabled'

    clear_btn = ttk.Button(logs_frame, text="Limpar Logs", command=clear_logs)
    clear_btn.grid(row=1, column=0, sticky='e', pady=5)
    return log_message
