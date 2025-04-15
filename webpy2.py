import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime

# Global stop flag
stop_flag = False

def send_messages(csv_file, progress_label, eta_label, cancel_btn):
    global stop_flag
    stop_flag = False
    cancel_btn.config(state="normal")
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV: {e}")
        return

    total = len(df)
    if total == 0:
        messagebox.showinfo("Done", "No contacts found in CSV.")
        return

    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://web.whatsapp.com")
    messagebox.showinfo("WhatsApp Web", "Scan the QR code, then click OK to continue...")

    start_time = time.time()

    for index, row in df.iterrows():
        if stop_flag:
            progress_label.config(text="Cancelled")
            break

        number = str(row['number'])
        message = str(row['message'])

        try:
            url = f"https://web.whatsapp.com/send?phone={number}&text={message}"
            driver.get(url)
            time.sleep(12)  # wait for WhatsApp to load

            send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
            send_btn.click()
            time.sleep(3)

        except Exception as e:
            print(f"[x] Failed for {number}: {e}")
            continue

        # Update progress bar and ETA
        done = index + 1
        percent = int((done / total) * 100)
        elapsed = time.time() - start_time
        eta = int((elapsed / done) * (total - done)) if done else 0
        eta_str = str(datetime.timedelta(seconds=eta))

        progress_label.config(text=f"{done}/{total} sent ({percent}%)")
        eta_label.config(text=f"ETA: {eta_str}")
        root.update()

    cancel_btn.config(state="disabled")
    if not stop_flag:
        messagebox.showinfo("Done", "All messages sent.")
    driver.quit()

def browse_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        csv_entry.delete(0, tk.END)
        csv_entry.insert(0, file_path)

def start_sending():
    csv_file = csv_entry.get()
    if not csv_file:
        messagebox.showwarning("Input needed", "Please select a CSV file.")
        return

    threading.Thread(target=send_messages, args=(csv_file, progress_label, eta_label, cancel_btn), daemon=True).start()

def cancel_sending():
    global stop_flag
    stop_flag = True
    cancel_btn.config(state="disabled")
    progress_label.config(text="Cancelling...")

# GUI
root = tk.Tk()
root.title("WhatsApp Bulk Messenger")
root.geometry("500x250")

tk.Label(root, text="Select CSV File:").pack(pady=5)
csv_entry = tk.Entry(root, width=50)
csv_entry.pack()
tk.Button(root, text="Browse", command=browse_csv).pack(pady=5)

tk.Button(root, text="Start Sending", command=start_sending).pack(pady=5)
cancel_btn = tk.Button(root, text="Cancel", command=cancel_sending, state="disabled")
cancel_btn.pack(pady=5)

progress_label = tk.Label(root, text="Progress: 0/0 (0%)")
progress_label.pack(pady=5)

eta_label = tk.Label(root, text="ETA: 00:00:00")
eta_label.pack(pady=5)

root.mainloop()
