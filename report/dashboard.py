import sys
from pathlib import Path

from fasthtml import FastHTML, serve
from fasthtml.common import *
import matplotlib.pyplot as plt
import pandas as pd

# Add the local python-package path so employee_events can be imported
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / 'python-package'))

# Import QueryBase, Employee, Team from employee_events
from employee_events import QueryBase, Employee, Team

# import the load_model function from the utils.py file
from .utils import load_model

"""
Below, we import the parent classes
you will use for subclassing
"""
from .base_components import (
    Dropdown,
    BaseComponent,
    Radio,
    MatplotlibViz,
    DataTable
    )

from .combined_components import FormGroup, CombinedComponent


# Create a subclass of base_components/dropdown
# called `ReportDropdown`
class ReportDropdown(Dropdown):

    def build_component(self, entity_id, model):
        self.label = model.name.title() if model.name else ''
        return super().build_component(entity_id, model)

    def component_data(self, entity_id, model):
        return model.names()


# Create a subclass of base_components/BaseComponent
# called `Header`
class Header(BaseComponent):

    def build_component(self, entity_id, model):
        return H1(f"{model.name.title()} Dashboard")


# Create a subclass of base_components/MatplotlibViz
# called `LineChart`
class LineChart(MatplotlibViz):

    def visualization(self, entity_id, model):
        data = model.event_counts(entity_id)
        data = data.fillna(0)
        data = data.set_index('event_date')
        data = data.sort_index()
        data = data.cumsum()
        data.columns = ['Positive', 'Negative']

        fig, ax = plt.subplots(figsize=(8, 4))
        data.plot(ax=ax)
        self.set_axis_styling(ax, bordercolor='black', fontcolor='black')
        ax.set_title('Cumulative Events Over Time')
        ax.set_xlabel('Event Date')
        ax.set_ylabel('Event Count')
        return ax


# Create a subclass of base_components/MatplotlibViz
# called `BarChart`
class BarChart(MatplotlibViz):

    predictor = load_model()

    def visualization(self, entity_id, model):
        data = model.model_data(entity_id)
        probabilities = self.predictor.predict_proba(data)[:, 1:]

        if model.name == 'team':
            pred = float(probabilities.mean())
        else:
            pred = float(probabilities[0, 0])

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh([''], [pred])
        ax.set_xlim(0, 1)
        ax.set_title('Predicted Recruitment Risk', fontsize=20)
        self.set_axis_styling(ax, bordercolor='black', fontcolor='black')
        return ax


# Create a subclass of combined_components/CombinedComponent
# called Visualizations       
class Visualizations(CombinedComponent):

    children = [LineChart(), BarChart()]

    # Leave this line unchanged
    outer_div_type = Div(cls='grid')
            
# Create a subclass of base_components/DataTable
# called `NotesTable`
class NotesTable(DataTable):

    def component_data(self, entity_id, model):
        return model.notes(entity_id)
    

class DashboardFilters(FormGroup):

    id = "top-filters"
    action = "/update_data"
    method="POST"

    children = [
        Radio(
            values=["Employee", "Team"],
            name='profile_type',
            hx_get='/update_dropdown',
            hx_target='#selector'
            ),
        ReportDropdown(
            id="selector",
            name="user-selection")
        ]
    
# Create a subclass of CombinedComponents
# called `Report`
class Report(CombinedComponent):

    children = [
        Header(),
        DashboardFilters(),
        Visualizations(),
        NotesTable(),
    ]

# Initialize a fasthtml app 
app = FastHTML()

# Initialize the `Report` class
report = Report()

# Create a route for a get request
# Set the route's path to the root
@app.get('/')
def index():
    # Call the initialized report
    # pass the integer 1 and an instance
    # of the Employee class as arguments
    # Return the result
    return report(1, Employee())

# Create a route for a get request
# Set the route's path to receive a request
# for an employee ID so `/employee/2`
# will return the page for the employee with
# an ID of `2`. 
# parameterize the employee ID 
# to a string datatype
@app.get('/employee/{id}')
def employee(id: str):
    # Call the initialized report
    # pass the ID and an instance
    # of the Employee SQL class as arguments
    # Return the result
    return report(id, Employee())

# Create a route for a get request
# Set the route's path to receive a request
# for a team ID so `/team/2`
# will return the page for the team with
# an ID of `2`. 
# parameterize the team ID 
# to a string datatype
@app.get('/team/{id}')
def team(id: str):
    # Call the initialized report
    # pass the id and an instance
    # of the Team SQL class as arguments
    # Return the result
    return report(id, Team())

# Keep the below code unchanged!
@app.get('/update_dropdown{r}')
def update_dropdown(r):
    dropdown = DashboardFilters.children[1]
    print('PARAM', r.query_params['profile_type'])
    if r.query_params['profile_type'] == 'Team':
        return dropdown(None, Team())
    elif r.query_params['profile_type'] == 'Employee':
        return dropdown(None, Employee())


@app.post('/update_data')
async def update_data(r):
    from fasthtml.common import RedirectResponse
    data = await r.form()
    profile_type = data._dict['profile_type']
    id = data._dict['user-selection']
    if profile_type == 'Employee':
        return RedirectResponse(f"/employee/{id}", status_code=303)
    elif profile_type == 'Team':
        return RedirectResponse(f"/team/{id}", status_code=303)
    


serve()
