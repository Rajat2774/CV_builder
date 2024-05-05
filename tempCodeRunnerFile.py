@app.route('/cv_filters')
def cv_filters():
    return render_template("filter.html")

# Flask route to handle CV filtering and display filtered CVs
@app.route('/apply_filters', methods=['POST'])
def apply_filters():
    if request.method == 'POST':
        # Retrieve filtering criteria from the form
        completion_status = request.form.get('completionStatus')
        person_info = request.form.get('prsn_info')
        education = request.form.get('education')
        language = request.form.get('Language')
        interest = request.form.get('Interest')
        achievement = request.form.get('Achievement')
        experience = request.form.get('Experience')
        project = request.form.get('Project')
        certificate = request.form.get('Certificates')

        # Query the database to filter CVs based on the criteria
        # Example:
        filtered_cvs = CV.query.filter_by(completion_status=completion_status).all()

        # Pass filtered CVs to HTML template for display
        return render_template("filtered_data.html", cvs=filtered_cvs)  



