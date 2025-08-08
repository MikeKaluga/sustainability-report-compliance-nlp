from translations import translate, switch_language

def switch_language_and_update_ui(app):
    """
    Switches the application language and updates all UI elements.
    """
    switch_language()
    update_ui_texts(app)
    refresh_current_display(app)

def update_ui_texts(app):
    """
    Updates all UI elements with the current language.
    """
    app.title(translate("app_title"))
    app.select_standard_btn.config(text=translate("select_standard"))
    app.select_report_btn.config(text=translate("select_report"))
    app.run_match_btn.config(text=translate("run_matching"))
    app.export_llm_btn.config(text=translate("export_llm_analysis"))
    app.analyze_llm_btn.config(text=translate("analyze_with_llm"))
    
    # Update status label based on current state
    if not app.standard_pdf_path:
        app.status_label.config(text=translate("initial_status"))
    elif not app.report_pdf_path:
        app.status_label.config(text=translate("standard_ready"))
    elif not app.matches:
        app.status_label.config(text=translate("report_ready"))
    else:
        app.status_label.config(text=translate("matching_completed_label"))

    # Update labels of the sub-menus inside the "Export" menu
    app.export_menu.entryconfig(0, label=translate("export_reqs"))
    app.export_menu.entryconfig(1, label=translate("export_paras"))
    app.export_menu.entryconfig(2, label=translate("export_matches"))
    
    # Update FAQ menu's sub-items
    app.faq_menu.entryconfig(0, label=translate("help"))
    app.faq_menu.entryconfig(1, label=translate("about"))

    app.list_container.config(text=translate("requirements_from_standard"))
    app.sub_point_container.config(text=translate("sub_points"))
    app.text_container.config(text=translate("requirement_text_and_matches"))

def refresh_current_display(app):
    """
    Refreshes the current display after language change.
    This ensures that any displayed text (like "run_matching_first") is updated.
    """
    if hasattr(app, 'current_req_code') and app.current_req_code:
        # Check if a sub-point is currently selected
        if hasattr(app, 'sub_point_listbox') and app.sub_point_listbox.curselection():
            sub_point_index = app.sub_point_listbox.curselection()[0]
            sub_point_text = app.sub_point_listbox.get(sub_point_index)
            # Refresh with the selected sub-point
            from event_handlers import handle_requirement_selection
            handle_requirement_selection(app, None, sub_point_text=sub_point_text.strip())
        else:
            # Refresh with the main requirement
            from event_handlers import handle_requirement_selection
            handle_requirement_selection(app, None)
