from translations import translate
import tkinter as tk

def handle_requirement_selection(app, event, sub_point_text=None):
    """
    Handles the selection of a requirement or sub-point, displaying the corresponding text and matches.
    If a sub-point is selected, it displays matches specific to that sub-point.
    """
    if sub_point_text:
        req_code = app.current_req_code
    else:
        if not app.req_listbox.curselection():
            return
        selected_index = app.req_listbox.curselection()[0]
        req_code = app.req_listbox.get(selected_index)
        app.current_req_code = req_code

    app.text_display.config(state="normal")
    app.text_display.delete("1.0", "end")

    if sub_point_text:
        print(f"Übergebener Sub-Point-Text: '{sub_point_text}'")

    # Default to disabled, enable only if matches are found
    app.analyze_llm_btn.config(state="disabled")

    if req_code in app.requirements_data:
        req_data = app.requirements_data[req_code]
        
        # Determine the text to display and the key to use for finding matches
        text_to_display = sub_point_text if sub_point_text else req_data['full_text']
        key_for_matches = text_to_display.strip()

        if app.matches and key_for_matches in app.matches:
            print(f"Schlüssel '{key_for_matches}' in app.matches gefunden.")
        else:
            print(f"Schlüssel '{key_for_matches}' NICHT in app.matches gefunden.")


        app.text_display.insert("end", translate("req_text_label") + "\n", "h1")
        app.text_display.insert("end", f"{text_to_display}\n\n")

        # Display matches if they exist
        if app.matches and key_for_matches in app.matches:
            app.text_display.insert("end", translate("matches_found_label") + "\n", "h1")
            
            match_list = app.matches.get(key_for_matches, [])

            if match_list:
                for report_idx, score in match_list:
                    app.text_display.insert("end", f"(Score: {score:.2f})\n", "score")
                    app.text_display.insert("end", f"{app.report_paras[report_idx]}\n\n")
                app.analyze_llm_btn.config(state="normal")
            else:
                app.text_display.insert("end", translate("no_matches_found"))
        else:
            # This case handles when matching hasn't been run yet.
            app.text_display.insert("end", translate("matches_found_label") + "\n", "h1")
            app.text_display.insert("end", translate("run_matching_first"))

    app.text_display.config(state="disabled")
    app.text_display.tag_config("h1", font=("Segoe UI", 12, "bold"), spacing1=5, spacing3=5)
    app.text_display.tag_config("score", font=("Segoe UI", 10, "italic"), foreground="blue")