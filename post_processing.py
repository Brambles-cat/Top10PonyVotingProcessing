"""Post-processing application."""

import sys
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.font import Font
from PIL import ImageTk, Image
from functions.post_processing import (
    fetch_videos_data,
    create_post_processed_records,
    generate_archive_records,
    generate_sharable_records,
    generate_archive_csv,
    generate_sharable_csv,
    generate_showcase_description,
)
from functions.messages import suc, inf, err


def browse_input_file():
    """Handler for the "Choose Input CSV" button. Opens a file dialog and sets the
    global variable `input_file_var` to the selected file."""
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    input_file_var.set(file_path)


def handle_post_processing():
    """Handler for the "Run post-processing" button."""
    input_file_str = input_file_var.get()
    if input_file_str.strip() == "":
        tk.messagebox.showinfo("Error", "Please select a CSV file to process.")
        return

    input_file_path = Path(input_file_str)
    output_dir = "outputs"
    output_file_prefix = "post-processed-"

    calc_records = []
    with input_file_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required_header = ["Title", "Percentage", "Total Votes", "URL"]
        if reader.fieldnames != required_header:
            err(
                f'Selected CSV file "{input_file_str}" has an invalid header: {",".join(reader.fieldnames)}'
            )
            tk.messagebox.showinfo(
                "Error",
                f"The selected CSV file is invalid. The file must have the following header line:\n\n{','.join(required_header)}",
            )
            return

        calc_records = [record for record in reader]

    inf("Performing post-processing...")

    video_urls = [record["URL"] for record in calc_records]
    videos_data = fetch_videos_data(video_urls)

    post_proc_records = create_post_processed_records(calc_records, videos_data)

    archive_file = f"{output_dir}/{output_file_prefix}archive.csv"
    sharable_file = f"{output_dir}/{output_file_prefix}sharable.csv"
    desc_file = f"{output_dir}/{output_file_prefix}description.txt"

    archive_records = generate_archive_records(post_proc_records)
    generate_archive_csv(archive_records, archive_file)
    suc(f"Wrote archive data to {archive_file}.")

    sharable_records = generate_sharable_records(post_proc_records)
    generate_sharable_csv(sharable_records, sharable_file)
    suc(f"Wrote sharable spreadsheet data to {sharable_file}.")

    showcase_desc = generate_showcase_description(post_proc_records)
    with open(desc_file, "w", encoding="utf8") as file:
        file.write(showcase_desc)

    suc(f"Wrote showcase description to {desc_file}.")
    suc("Finished.")

    tk.messagebox.showinfo(
        "Success",
        f"Post-processing complete. The following output files have been created:\n\n{archive_file}\n{sharable_file}\n{desc_file}",
    )


# Create application window
root = tk.Tk()
root.title("Top 10 Pony Videos: Post-processing")
root.geometry(f"800x400")

# Create main frame
main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill="both", padx=10, pady=10)

# Create banner image
banner_image = ImageTk.PhotoImage(Image.open("images/post-processing.png"))
banner_label = tk.Label(main_frame, image=banner_image)
banner_label.pack()

# Create title
title_font = Font(size=16)
title_label = tk.Label(main_frame, font=title_font, text="Post-processing")
title_label.pack(pady=8)

# Create "Choose Input CSV..." control
input_file_frame = tk.Frame(main_frame)
input_file_label = tk.Label(input_file_frame, text="Input CSV file:")

default_input_file = "outputs/calculated_top_10.csv"
input_file_var = tk.StringVar()
input_file_var.set(default_input_file)
input_file_entry = ttk.Entry(input_file_frame, width=40, textvariable=input_file_var)

browse_button = ttk.Button(
    input_file_frame, text="📁 Choose Input CSV...", command=browse_input_file
)

input_file_label.grid(column=0, row=0, padx=5, pady=5)
input_file_entry.grid(column=1, row=0, padx=5, pady=5)
browse_button.grid(column=2, row=0, padx=5, pady=5)

input_file_frame.pack()

# Create buttons bar
buttons_frame = tk.Frame(main_frame)
buttons_frame.pack()

run_button = ttk.Button(
    buttons_frame, text="🏁 Run Post-processing", command=handle_post_processing
)
run_button.grid(column=0, row=0, padx=5, pady=5)

quit_button = ttk.Button(buttons_frame, text="Quit", command=root.destroy)
quit_button.grid(column=1, row=0, padx=5, pady=5)

root.mainloop()
