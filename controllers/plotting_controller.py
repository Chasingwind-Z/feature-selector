class PlottingController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        # Connect view actions to controller methods
        self.view.plot_requested.connect(self.handle_plot_request)

    def handle_plot_request(self, plot_type, params):
        """Handle the request to generate a plot based on the plot type and additional parameters."""
        try:
            if plot_type == "Missing Values":
                self.view.plot_missing()
            elif plot_type == "Unique Values":
                self.view.plot_unique()
            elif plot_type == "Collinear Features":
                self.view.plot_collinear(params.get('plot_all', False))
            elif plot_type == "Feature Importances":
                plot_n = params.get('plot_n', 15)
                threshold = params.get('threshold', None)
                self.view.plot_feature_importances(plot_n, threshold)
        except Exception as e:
            self.view.message_label.setText(f"Error: {str(e)}")

# Usage (somewhere in your main application logic):
# model = PlottingModel(...)
# view = PlottingView(...)
# controller = PlottingController(model, view)
