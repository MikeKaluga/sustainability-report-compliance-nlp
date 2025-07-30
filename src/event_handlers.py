from translations import translate

def handle_requirement_selection(app, event):
    """
    Handles the selection of a requirement from the listbox and displays its matches.
    """
    selected_indices = app.req_listbox.curselection()
    if not selected_indices:
        return

    index = selected_indices[0]
    selected_code = app.req_listbox.get(index)
    req_text = app.requirements_data.get(selected_code, "Text not found.")

    app.text_display.config(state="normal")
    app.text_display.delete("1.0", "end")

    app.text_display.insert("end", translate("req_text_label") + "\n", "h1")
    app.text_display.insert("end", f"{req_text}\n\n")

    if app.matches and index < len(app.matches):
        app.text_display.insert("end", translate("matches_found_label") + "\n", "h1")
        match_list = app.matches[index]
        if not match_list:
            app.text_display.insert("end", translate("no_matches_found"))
            app.analyze_llm_btn.config(state="disabled")
        else:
            for report_idx, score in match_list:
                app.text_display.insert("end", f"(Score: {score:.2f})\n", "score")
                app.text_display.insert("end", f"{app.report_paras[report_idx]}\n\n")
            app.analyze_llm_btn.config(state="normal")
    else:
        app.analyze_llm_btn.config(state="disabled")

    app.text_display.config(state="disabled")
    app.text_display.tag_config("h1", font=("Segoe UI", 12, "bold"), spacing1=5, spacing3=5)
    app.text_display.tag_config("score", font=("Segoe UI", 10, "italic"), foreground="blue")
