import tkinter as tk
from processing.priorities_processor import set_process_priority

def create_tkinter_controls(controls):

    set_process_priority("below_normal")
    root = tk.Tk()
    root.title("Controles Adicionais")

    for flag in ["SHOW_VIDEO", "SHOW_EDGES", "SHOW_ROI", "SHOW_PERSON_DETECTION"]:
        controls.setdefault(flag, True)

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    def toggle_show_video():
        controls["SHOW_VIDEO"] = not controls["SHOW_VIDEO"]
        print("SHOW_VIDEO:", controls["SHOW_VIDEO"])

    def toggle_show_edges():
        controls["SHOW_EDGES"] = not controls["SHOW_EDGES"]
        print("SHOW_EDGES:", controls["SHOW_EDGES"])

    def toggle_show_roi():
        controls["SHOW_ROI"] = not controls["SHOW_ROI"]
        print("SHOW_ROI:", controls["SHOW_ROI"])

    def toggle_show_person_detection():
        controls["SHOW_PERSON_DETECTION"] = not controls["SHOW_PERSON_DETECTION"]
        print("SHOW_PERSON_DETECTION:", controls["SHOW_PERSON_DETECTION"])


    if not controls["WEBVIEW"]:
        btn_video = tk.Button(frame, text="Toggle SHOW_VIDEO", command=toggle_show_video)
        btn_video.pack(side=tk.LEFT, padx=5)

        btn_edges = tk.Button(frame, text="Toggle SHOW_EDGES", command=toggle_show_edges)
        btn_edges.pack(side=tk.LEFT, padx=5)

        btn_roi = tk.Button(frame, text="Toggle SHOW_ROI", command=toggle_show_roi)
        btn_roi.pack(side=tk.LEFT, padx=5)

    btn_person_detection = tk.Button(frame, text="Toggle PERSON_DETECTION", command=toggle_show_person_detection)
    btn_person_detection.pack(side=tk.LEFT, padx=5)

    root.mainloop()