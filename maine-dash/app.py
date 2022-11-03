#!/usr/bin/env python
# coding: utf-8

# cache: named tuple process_all_voters_table_callback cache table_row

# use aws for a mail form
# add multiindex for voter1/voter2 table

if __name__ == "__main__":
    NAME = "MAIN"
else:
    NAME = "CLOUD"

# constants
run_dash_mode = True
# run_dash_mode = False
use_data_subsets = True
use_data_subsets = False
dash_app_name = "JupyterDash"
dash_app_name = "Dash"
dev_mode = True
# dev_mode = False
prod_mode = True
# prod_mode = False
if dash_app_name == "JupyterDash":
    dev_mode = False
if prod_mode:
    dev_mode = False
    # deactivate; source venv_maine_analysis/bin/activate; jupyter nbconvert maine_analysis.ipynb --to python; deactivate; source venv_maine_analysis_prod/bin/activate; python maine_analysis.py
    # DEST=deploy_mobile; cp maine_analysis.py ${DEST}/main.py; cp -r exports ${DEST}; cp deploy.sh ${DEST}; cp Dockerfile ${DEST}; cp requirements_prod_long.txt ${DEST}
# test: jupyter nbconvert maine_analysis.ipynb --to python; python maine_analysis.py
#

# conditionals

if prod_mode:
    exports = "."
else:
    exports = "exports"

# imports

import json
import copy
import sys
import os
import datetime

if dev_mode:
    from icecream import ic
else:
    def ic(*args, **kwargs):
        return args

if not prod_mode:
    from jupyter_dash import JupyterDash

import pandas as pd

import plotly.express as px
import dash
from dash.dash_table import DataTable
from dash import  dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

import logging # Basic config below is used for MS Code compatibility
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

# if not run_dash_mode:
logging.basicConfig(stream=sys.stderr)
# else:
#     logging.basicConfig(filename='dash.log')

LOG.info("Logging (info) has been initialized")
LOG.debug("Logging (debug) has been initialized")

# define methods:
if True: # define & test functions
    # @TODO: import/export df not super clean
    if True:
        # def export_df(dataframe):
        def export_df(dataframe=None, df=None, filename=None, index=True):
            if dataframe is not None:
                df = globals()[dataframe]
                filename = dataframe
            filename = os.path.join(exports, f"{filename}.csv")
            df.to_csv(filename, index=index)

        def import_df(dataframe):
            filename = os.path.join(exports, f"{dataframe}.csv")
            df = pd.read_csv(filename, index_col=0)
            return df

        def export_dict(dictionary_name):
                dictionary = globals()[dictionary_name]
                filename = os.path.join(exports, f"{dictionary_name}.json")
                with open(filename, 'w') as _file:
                    json.dump(dictionary, _file)

        def import_dict(dictionary_name):
            filename = os.path.join(exports, f"{dictionary_name}.json")
            with open(filename) as _file:
                result = json.load(_file)
            return result

        def get_party_lean(party, polarization):
            if party == "Democratic":
                party_lean = "Democratic"
            elif party == "Republican":
                party_lean = "Republican"
            elif polarization < 0.5:
                party_lean = "Democratic"
            else:
                party_lean = "Republican"
            return party_lean

        class SimpleDashTable():

            def __init__(
                self, df,
                table_style=None,
                column_specification=None,
                delete_columns=[],
                column_order=[],
                column_specs={},
                column_name_transform=None,
                dash_id=None,
                sortable_table_options={},
                empty=False,
                ):
                self.df = df.copy()
                self.table_style = table_style
                self.column_specification = column_specification
                self.delete_columns = delete_columns
                self.column_order = column_order
                self.column_specs = column_specs
                self.column_name_transform = column_name_transform
                self.dash_id = dash_id
                self.id = dash_id
                self.sortable_table_options=sortable_table_options
                self.empty = empty

                self.update_table_data()
                self.update_tables()

            def update_table_data(self):
                # begin update:
                if self.column_order:
                    self.delete_columns = [
                        column for column in self.df.columns
                        if column not in set(self.column_order)]
                if self.delete_columns:
                    self.df = self.df.drop(columns=self.delete_columns)
                if self.column_order:
                    self.df = self.df[self.column_order]
                if self.column_specification == None:
                    self.column_specification = self.default_column_specification

                self.columns = [
                    self.column_specification(
                        id, name,
                        self.column_name_transform(name),
                        column_specs=self.column_specs)
                    for id, name in enumerate(self.df.columns)]
                original_columns = self.df.columns
                self.df.columns = (
                    [f"c{id}" for id, name in enumerate(self.df.columns)])
                self.data = self.df.to_dict('records')
                self.df.columns = original_columns
                self.column_lookup = (
                    {name: f"c{id}" for id, name in enumerate(self.df.columns)})

            def export_df(self, filename):
                export_df(dataframe=None, df=self.df, filename=filename)

            def update_tables(self):
                table_dict = {
                    "data": self.data,
                    "columns": self.columns,
                }
                if self.table_style is not None:
                    table_dict["style_cell"] = self.table_style
                    # table_dict["style_data_conditional"] = {
                    #     'if': {'row_index': 'odd'},
                    #     'backgroundColor': 'rgb(232, 232, 232)'}
                    self.static_table = dash_table.DataTable(**table_dict)

                if self.dash_id == None:
                    self.sortable_table = dcc.Markdown("A sortable table requires an dash_id.")
                else:
                    # dash_table.DataTable(
                    sortable_table_dict = copy.copy(table_dict)
                    sortable_table_default_options = dict(
                        id=self.dash_id,
                        filter_action="native",
                        filter_options={"case":"insensitive"},
                        sort_action="native",
                        sort_mode="single",
                        selected_columns=[],
                        selected_rows=[],
                        page_action="native",
                        page_current= 0,
                        page_size= 10,
                        )
                    if self.empty:
                        sortable_table_dict["data"] = []
                        sortable_table_dict["columns"] = []
                    sortable_table_dict.update(sortable_table_default_options)
                    sortable_table_dict.update(self.sortable_table_options)
                    self.sortable_table = dash_table.DataTable(**sortable_table_dict)

            @staticmethod
            def default_column_specification(id, full_name, short_name, column_specs={}):
                result = {"name": short_name, "id": f"c{id}"}
                if full_name in column_specs.keys():
                    result.update(column_specs[full_name])
                return result
                    # "type": "numeric",
                    # "format": dash_table.FormatTemplate.percentage(1)}
            pass

        def get_voter_polarization_fig(
            df,
            voter1=None,
            voter2=None,
            ):
            xvar = "Polarization"
            yvar = "Party agreement"
            fig = px.scatter(
                    df,
                    x=xvar,
                    y=yvar,
                    color="Party",
                    hover_data = {
                        'Name': True,
                        'Party': True,
                        'Seat': True,
                        'Polarization': ":,.0%",
                        'Party agreement': ":,.0%",
                    },
                )
            fig.update_layout(yaxis_tickformat = ',.0%')
            fig.update_layout(xaxis_tickformat = ',.0%')
            # @TODO: combine the next two conditionals
            if voter1:
                fig.add_annotation(
                    x=voter1[xvar],
                    y=voter1[yvar],
                    text=voter1["name"],
                    yanchor='bottom',
                    showarrow=True,
                    arrowhead=1,
                    arrowsize=1,
                    arrowwidth=2,
                    ax=-.7,
                    ay=.71,
                    axref="x",
                    ayref="y",
                    # axref="x domain",
                    # ayref="y domain",
                    # xref="x domain",
                    # yref="y domain",
                    align="center",
                    )
            if voter2:
                fig.add_annotation(
                    x=voter2[xvar],
                    y=voter2[yvar],
                    text=voter2["name"],
                    yanchor='top',
                    showarrow=True,
                    arrowhead=1,
                    arrowsize=1,
                    arrowwidth=2,
                    ax=.7,
                    ay=.69,
                    axref="x",
                    ayref="y",
                    align="center",
                    )
            fig.update_layout(
                font_family="Helvetica",
            )
            return fig

        def get_vote_polarization_fig(df):
            df2 = df.rename(columns={"Party polarization": "Party<br>polarization"})
            fig = px.scatter(
                df2,
                x="Republican yes",
                y = "Democratic yes",
                symbol="Session",
                color="Party<br>polarization",
                color_continuous_scale=["blue", "red"],
                hover_data = {
                    'title_w_breaks': True,
                    'Date': True,
                    'Session': True,
                    'Party<br>polarization': ":,.0%",
                },
                labels={"title_w_breaks": "Title"},
            )
            fig.update_layout(yaxis_tickformat=',.0%')
            fig.update_layout(xaxis_tickformat=',.0%')
            fig.update_coloraxes(colorbar_tickformat=',.0%')
            fig.update_layout(legend_orientation="h")
            fig.update_layout(
                font_family="Helvetica",
            )
            return fig

# formating
if True: # lookup of mobile column headers
    mobile_lookup_dict = {
        "Polarization": "Polar-\nization",
        "Vote polarization": "Vote\npolar-\nization",
        "Vote-1 polarization": "Vote-1\npolar-\nization",
        "Vote-2 polarization": "Vote-2\npolar-\nization",
        "Democratic votes yes/no": "Demo-\ncratic\nvotes\nyes/no",
        "Republican votes yes/no": "Repub-\nlican\nvotes\nyes/no",
        "Democratic agreement": "Demo-\ncratic\nagree-\nment",
        "Republican agreement": "Repub-\nlican\nagree-\nment",
    }
    def column_name_transform(value, mobile=False):
        if not mobile:
            return value
        return mobile_lookup_dict.get(value, value)

if True: # formatting constants
    date_format = "%Y-%m-%d"
    default_column_specs = {
        "Vote polarization": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Vote-1 polarization": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Vote-2 polarization": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Polarization": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Democratic agreement": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Republican agreement": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Session 128": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Session 129": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        "Session 130": {
            "type": "numeric",
            "format": dash_table.FormatTemplate.percentage(0)},
        }


# define dash mode functions

if run_dash_mode: # tabs
    # search markdown
    def run_dash(port, mobile):
        """Run voter dash in either mobile or non-mobile mode."""
        # constants
        state = "Maine"

        # mobile/non mobile
        if mobile:
            table_style = {
                'font-size':'2.5vmin',
                'font-family':'sans-serif',
                'whiteSpace': 'pre-line',
            }
        else:
            table_style = {
                # 'font-size':'2vmin',
                'font-family':'sans-serif',
                'whiteSpace': 'pre-line',
            }

        independent_table_columns = [
            "Vote",
            "Vote polarization",
            "Democratic votes yes/no",
            "Republican votes yes/no",
            "Title",
            "Date"]

        if True: # Load data
            vote_polarization_df = import_df(f"vote_polarization_df")
            voter_polarization_df = import_df(f"voter_polarization_df")
            voter_polarization_highlights = import_df(f"voter_polarization_highlights_df")
            voter_polarization_dash_table_df = import_df(f"voter_polarization_dash_table_df")
            voting_statistics_df = import_df("voting_statistics_df")
            head_to_head_sorted_df = import_df("head_to_head_df")

            bill_lookup = import_dict(f"bill_lookup")
            voter_bills_dict = import_dict(f"voter_bills_dict")
            dash_table_lookup = import_dict(f"dash_table_lookup")
            voter_bills_heap_export = import_dict(f"voter_bills_heap_export")

            if NAME == "MAIN":
                # all votes:
                all_votes_table = vote_polarization_df[[
                    'Key', 'Yes polarization', 'Democratic yes votes', 'Democratic no votes',
                    'Republican yes votes', 'Republican no votes', 'Title', 'Date', 'Session']]
                all_votes_table = all_votes_table.rename(columns={
                    "Key": "Vote key", "Yes polarization": "Vote polarization"})
                export_df(None, all_votes_table, "all_votes_table_v2", index=False)
                all_voters_table = voter_polarization_df[[
                    "Key", "Name", "Seat", "Party", "Polarization",
                    "Democratic agreement", "Republican agreement"]]
                all_voters_table = all_voters_table.rename(columns={"Key": "Voter key"})
                export_df(None, all_voters_table, "all_voters_table", index=False)
                columns = ["Voter key", "Vote key", "Vote"]
                data = []
                for voter_key, votes in voter_bills_dict.items():
                    for vote_key, vote in votes.items():
                        data.append([voter_key, vote_key, vote])
                df = pd.DataFrame(data=data, columns=columns)
                export_df(None, df, "all_voters_and_votes", index=False)
            pass
        if True: # Debug data load
            # key = "LAROCHELLE OF AUGUSTA"
            # print(voter_bills_heap_export[key])
            # bill_key = voter_bills_heap_export[key]["min_heap"][0][1]
            # print(bill_lookup[bill_key])
            # sys.exit()
            pass
        if True: # Build static figures and tables
            vote_polarization_fig = get_vote_polarization_fig(
                vote_polarization_df[vote_polarization_df["Party"] == "Democratic"])

            voter_highlight_table = SimpleDashTable(
                voter_polarization_highlights,
                table_style,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                column_specs=default_column_specs,
                )
            head_to_head_table = SimpleDashTable(
                head_to_head_sorted_df,
                table_style,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                column_specs=default_column_specs,
                )
            voting_statistics_table = SimpleDashTable(
                voting_statistics_df,
                table_style,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                column_specs = default_column_specs,
                )

            all_voters_table = SimpleDashTable(
                (voter_polarization_dash_table_df[:5]
                    if use_data_subsets
                    else voter_polarization_dash_table_df),
                table_style,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                dash_id='all_voters_table',
                column_specs = default_column_specs,
                sortable_table_options = {
                    "row_selectable": "single",
                    "page_size": 3},
                )

            all_voters_table2 = SimpleDashTable(
                (voter_polarization_dash_table_df[:5]
                    if use_data_subsets
                    else voter_polarization_dash_table_df),
                table_style,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                dash_id='all_voters_table2',
                column_specs = default_column_specs,
                sortable_table_options = {
                    "row_selectable": "single",
                    "page_size": 3},
                )
            vote_polarization_df["Vote polarization"] = vote_polarization_df['Yes polarization']
            all_votes_table = SimpleDashTable(
                (vote_polarization_df[:5] if use_data_subsets else vote_polarization_df),
                table_style,
                column_order = [
                    "Vote polarization",
                    "Democratic votes yes/no",
                    "Republican votes yes/no",
                    "Title",
                    "Date",
                ],
                column_specs = default_column_specs,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                dash_id='all_votes_table',
            )
            first_year_copyright = 2022
            current_year = datetime.datetime.now().year
            if current_year > first_year_copyright:
                copyright_date = f"{first_year_copyright}-{current_year}"
            else:
                copyright_date = f"{current_year}"

            feedback_string = f"""
                Processed data is available for [all voters](
                https://storage.googleapis.com/dash-polarization/all_voters_table_v2.csv),
                [all votes](
                https://storage.googleapis.com/dash-polarization/all_votes_table_v2.csv),
                and [all voters and their votes](
                https://storage.googleapis.com/dash-polarization/all_voters_and_votes.csv).
                This data was processed from [openstates.org](https://openstates.org) records on
                [legislation](https://openstates.org/me/bills/) and [people](
                https://github.com/openstates/people).
                The polarization of a vote is defined by the difference between
                percentage of Republican yes votes and the percentage of
                Democratic yes votes. Questions, comments, corrections? Please
                email
                [questions@democracygps.org](mailto:questions@democracygps.org).
                This website was produced by democracyGPS, a not-for-profit
                electronic democracy company based near Oakland, California.

                Copyright {copyright_date}, democracyGPS.
                Commercial use, modification, distribution, and private use of
                data and figures from this website is freely allowed under the
                [MIT License](https://storage.googleapis.com/dash-polarization/LICENSE.txt).
                """
        if True: # Build template for all votes table
            vote_polarization_voter = vote_polarization_df.copy()
            vote_polarization_voter["Vote-1"] = vote_polarization_voter["Key"]
            vote_polarization_voter["Vote-1 polarization"] = vote_polarization_voter["Key"]
            vote_polarization_voter["Vote-2"] = vote_polarization_voter["Key"]
            vote_polarization_voter["Vote-2 polarization"] = vote_polarization_voter["Key"]
            voter_all_votes_table = SimpleDashTable(
                (vote_polarization_voter[:5] if use_data_subsets else vote_polarization_voter),
                table_style,
                column_order = [
                    "Vote-1",
                    "Vote-1 polarization",
                    "Vote-2",
                    "Vote-2 polarization",
                    "Democratic votes yes/no",
                    "Republican votes yes/no",
                    "Title",
                    "Date",
                ],
                column_specs = default_column_specs,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                dash_id='voter_all_votes_table',
                empty=True,
            )
            pass

        # Build App
        # app = JupyterDash(
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
        )
        tab1_content = dbc.Card(
            dbc.CardBody(
                [
                    html.Img(src="assets/DemocracyGPS-logo-forWeb.svg",
                        style={"width": "50%", "justify-content": "flex-end"}),
                    html.Div([  # Voting histories for Maine state politicians"
                        dcc.Markdown(f"""
                            # Voting histories for Maine state politicians

                            This website allows you to easily search the voting history
                            of current and recent Maine state senators and representatives.
                            It also allows you to compare the voting histories of any two
                            state politicians, provides a measure of political
                            polarization of each politician, and shows which bills were
                            most polarizing.
                            """),
                        dcc.Markdown(f"""
                            Please choose one or two politicians below.
                            Only politicians who have previously been in the
                            Maine Senate or House
                            can be chosen.
                            """),
                    ]),
                    html.Div([  ## Table of all Politician
                        dcc.Markdown(f"""
                            ### Politician # 1

                            Click on arrows to sort columns. Type name, city, etc.
                            in 'filter data...' row followed by <return> to search.
                            Click on the circle to the left of a politician's row
                            to select.
                        """),
                        all_voters_table.sortable_table,
                    ]),
                    html.Div([  ## Table of all politicians
                        html.Br(),
                        dcc.Markdown(f"""
                            ### Politician # 2

                            Click on arrows to sort columns. Type name, city, etc.
                            in 'filter data...' row followed by <return> to search.
                            Click on the circle to the left of a politician's row
                            to select.
                        """),
                        all_voters_table2.sortable_table,
                    ]),
                    html.Br(),
                    html.Div([  # {state} politician polarization from 2017 to 2022
                        dcc.Markdown(f"""
                            ### {state} politician polarization from 2017 to 2022

                            Democratic polarization is to the left. Republican
                            polarization is to the right. Hover your mouse/pointer
                            over the data points for more information on each
                            politician.
                            """),
                        dcc.Graph(id="dynamic_voter_polarization_fig"),
                    ]),
                    html.Div(id='independent_votes1'),
                    html.Div(id='independent_votes2'),
                    html.Div([  ## Table of all votes
                        html.Div(id='voter_all_votes_table_header'),
                        html.Div(voter_all_votes_table.sortable_table),
                        html.Div(id='voter_all_votes_table_output'),
                        # id='full_vote_table_subtables'),
                    ]),
                    html.Div([  ## Table of the most and least polarized politicians
                        dcc.Markdown(f"""
                            ### Table of the most and least polarized politicians

                            Norman Higgins of Dover-Foxcroft is the least
                            polarized, having voted with the majority of both
                            Democrats and Republicans 60-62% of the time. Cathy
                            Nadeau of Winslow and Stephen Stanley of Augusta
                            (retired) although both Republicans, voted with the
                            Democratic majority more frequently than with the
                            Republican majority. Negative polarization leans
                            toward the Democratic party. Positive polarization leans
                            toward the Republican party.
                            """),
                        voter_highlight_table.static_table,
                        html.Br(),
                        dcc.Markdown(f"""
                            Finally, below is a head-to-head voting comparison
                            of 14 candidates running against each other this
                            November who both have been in the Senate or House
                            during the last 3 Legislative sessions.
                            """),
                        head_to_head_table.static_table,
                        html.Br(),
                    ]),
                    dcc.Markdown(feedback_string),
                ]
            ),
            className="mt-3",
        )
        tab2_content = dbc.Card(
            dbc.CardBody(
                [
                    html.Img(src="assets/DemocracyGPS-logo-forWeb.svg",
                        style={"width": "50%", "justify-content": "flex-end"}),
                    html.Div([  # Which bills were most polarizing?
                        dcc.Markdown(f"""
                            # Which bills were most polarizing?

                            {state} bill polarization from 2017 to 2022.
                            Bills with a majority Republican support are in the lower right
                            (polarization is close to +100%).
                            Bills with a majority Democratic support are in the upper left
                            (polarization is close to -100%).
                            Bills with bipartisan support are in the upper right
                            (polarization is close to 0%).
                            Hover your mouse/pointer over the data points for more information
                            on each bill.
                            """),
                        dcc.Graph(figure=vote_polarization_fig),
                    ]),
                    html.Div([  # Polarization in {state} has increased
                        dcc.Markdown(f"""
                            ## Polarization in {state} has increased between 2017 and 2022

                            The percentage of bipartisan votes has decreased, the
                            percentage of polarized votes has increased, and average
                            polarization has increased. Some, but not necessarily all,
                            of this increase is due to Republican politicians starting
                            to vote more unanimously (like their Democratic colleagues).
                            """),
                        voting_statistics_table.static_table,
                        html.Br(),
                    ]),
                    html.Div([  # Table of all votes
                        dcc.Markdown(f"""
                            ## Table of all votes

                            Click on arrows to sort columns. Type a word or
                            phrase in the title box in the 'filter data...' row
                            followed by <return> to search. his or her voting
                            record. Negative vote polarization leans toward the
                            Democratic party. Positive vote polarization leans
                            toward the Republican party.
                            """),
                        all_votes_table.sortable_table,
                        html.Br(),
                        html.Div(id='all_votes_table_output'),
                    ]),
                    dcc.Markdown(feedback_string),

                ]
            ),
            className="mt-3",
        )
        app.layout = dbc.Tabs(
            [
                dbc.Tab(tab1_content, label=f"Voting histories"),
                dbc.Tab(tab2_content, label=f"Bill polarization"),
            ]
        )
        # Callbacks
        def process_all_voters_table_callback(df, derived_virtual_selected_rows):
            """Process callback row for all_voters_table."""
            # LOG.info(df)
            # LOG.info(derived_virtual_selected_rows)
            table_row = df.iloc[derived_virtual_selected_rows[0]]
            # LOG.info(table_row)
            name_column = all_voters_table.column_lookup['Name']
            city_column = all_voters_table.column_lookup['City']
            party_column = all_voters_table.column_lookup['Party']
            party = table_row[party_column]
            polarization_column = all_voters_table.column_lookup["Polarization"]
            democratic_agreement_column = all_voters_table.column_lookup["Democratic agreement"]
            republican_agreement_column = all_voters_table.column_lookup["Republican agreement"]
            voter_name = f"{table_row[name_column]} of {table_row[city_column]}".replace("\n", "")
            voter_last_name = table_row[name_column].split(",")[0]
            voter_key = dash_table_lookup[voter_name]["Key"]
            full_name_and_city = dash_table_lookup[voter_name]["full_name_and_city"]
            party_lean = get_party_lean(party, table_row[polarization_column])
            voter_initial = full_name_and_city[:1]
            result = dict(
                table_row = table_row,
                name_column = name_column,
                city_column = city_column,
                party_column = party_column,
                polarization_column = polarization_column,
                voter_name = voter_name,
                voter_last_name = voter_last_name,
                voter_key = voter_key,
                full_name_and_city = full_name_and_city,
                name_and_initial = f"{voter_initial}. {voter_last_name}",
                party_lean = party_lean,
                Polarization = table_row[polarization_column],
                Party = party,
                )
            result["Democratic agreement"] = table_row[democratic_agreement_column]
            result["Republican agreement"] = table_row[republican_agreement_column]
            return result

        @app.callback(
            Output('voter_all_votes_table_output', "children"),
            Input(voter_all_votes_table.id, "derived_virtual_data"),
            Input(voter_all_votes_table.id, "derived_virtual_selected_rows"))
        def update_voter_all_votes_table(table_rows, derived_virtual_selected_rows):
            """
            Dummy update.

            This callback enables sorting and filtering in(voter_all_votes_table.
            """
            return html.Div()

        @app.callback(
            Output('all_votes_table_output', "children"),
            Input(voter_all_votes_table.id, "derived_virtual_data"),
            Input(voter_all_votes_table.id, "derived_virtual_selected_rows"))
        def update_all_votes_table(table_rows, derived_virtual_selected_rows):
            """
            Dummy update.

            This callback enables sorting and filtering in(voter_all_votes_table.
            """
            return html.Div()

        # update figure
        @app.callback(
            Output("dynamic_voter_polarization_fig", "figure"),
            Input(all_voters_table.id, "derived_virtual_data"),
            Input(all_voters_table.id, "derived_virtual_selected_rows"),
            Input(all_voters_table2.id, "derived_virtual_data"),
            Input(all_voters_table2.id, "derived_virtual_selected_rows"),
            )
        def update_dynamic_voter_polarization_fig(
            table_rows1, derived_virtual_selected_rows1,
            table_rows2, derived_virtual_selected_rows2,
            ):
            """Update all votes table header (empty to start.)"""
            voter1, voter2 = None, None
            # @TODO combine the next two conditionals
            callback_data1, callback_data2 = process_double_callback(
                table_rows1, derived_virtual_selected_rows1,
                table_rows2, derived_virtual_selected_rows2,
                )
            if callback_data1:
                voter1 = {}
                # voter1["name"] = callback_data1["full_name_and_city"]
                # voter1["name"] = voter1["name"].replace(" of ","<br>of ")
                voter1["name"] = callback_data1["name_and_initial"]
                voter1["Polarization"] = callback_data1["Polarization"]
                if voter1["Polarization"] < 0:
                    voter1["Party agreement"] = callback_data1["Democratic agreement"]
                else:
                    voter1["Party agreement"] = callback_data1["Republican agreement"]
            if callback_data2:
                voter2 = {}
                # voter2["name"] = callback_data2["full_name_and_city"]
                # voter2["name"] = voter2["name"].replace(" of ","<br>of ")
                voter2["name"] = callback_data2["name_and_initial"]
                voter2["Polarization"] = callback_data2["Polarization"]
                if voter2["Polarization"] < 0:
                    voter2["Party agreement"] = callback_data2["Democratic agreement"]
                else:
                    voter2["Party agreement"] = callback_data2["Republican agreement"]
            if (callback_data1 and callback_data2 and
                callback_data1["full_name_and_city"]
                == callback_data2["full_name_and_city"]):
                voter2 = None
            # cases: ab a b none
            if not voter2:
                if voter1 and voter1["Polarization"] > 0:
                    voter1, voter2 = None, voter1
            elif voter1 is not None and voter2 is not None:
                if voter1["Polarization"] > voter2["Polarization"]:
                    voter1, voter2 = voter2, voter1

            return get_voter_polarization_fig(
                voter_polarization_df,
                voter1=voter1,
                voter2=voter2)

        def process_double_callback(
            table_rows, derived_virtual_selected_rows,
            table_rows2, derived_virtual_selected_rows2,
            ):
            callback_data, callback_data2 = None, None
            if derived_virtual_selected_rows:
                callback_data = process_all_voters_table_callback(
                    pd.DataFrame(table_rows), derived_virtual_selected_rows)

            if derived_virtual_selected_rows2:
                callback_data2 = process_all_voters_table_callback(
                    pd.DataFrame(table_rows2), derived_virtual_selected_rows2)
            if (callback_data and callback_data2 and
                callback_data["full_name_and_city"]
                == callback_data2["full_name_and_city"]):
                callback_data2 = None
            if not callback_data:
                callback_data, callback_data2 = callback_data2, callback_data
            return callback_data, callback_data2

        @app.callback(
            Output("voter_all_votes_table_header", "children"),
            Input(all_voters_table.id, "derived_virtual_data"),
            Input(all_voters_table.id, "derived_virtual_selected_rows"),
            Input(all_voters_table2.id, "derived_virtual_data"),
            Input(all_voters_table2.id, "derived_virtual_selected_rows"),
            )
        def update_all_votes_table_header(
            table_rows, derived_virtual_selected_rows,
            table_rows2, derived_virtual_selected_rows2,
            ):
            """Update all votes table header (empty to start.)"""
            # @TODO: change to
            if (not derived_virtual_selected_rows
               or not derived_virtual_selected_rows):
            # if not derived_virtual_selected_rows:
                return [dcc.Markdown("")]

            callback_data, callback_data2 = process_double_callback(
                table_rows, derived_virtual_selected_rows,
                table_rows2, derived_virtual_selected_rows2,
                )

            full_name_and_city = callback_data["full_name_and_city"]
            full_name_and_city_header = f"{callback_data['full_name_and_city']} (Vote-1)"
            party_text = f"a member of the {callback_data['Party']} party"
            if callback_data2:
                full_name_and_city = (
                    f"{callback_data['full_name_and_city']} and "
                    f"{callback_data2['full_name_and_city']}")
                full_name_and_city_header = (
                    f"{callback_data['full_name_and_city']} (Vote-1) and "
                    f"{callback_data2['full_name_and_city']} (Vote-2)")
                party_text = (
                    f"members of the {callback_data['Party']} "
                    f"and {callback_data2['Party']} parties")

            all_votes_header = dcc.Markdown(f"""
                ### All votes for {full_name_and_city_header}

                All bills that
                {full_name_and_city}, {party_text}
                voted on between 2017 and 2022 (legislative
                sessions of 128, 129 or 130). Click on arrows to sort columns.
                Type a word or phrase in the title box in the 'filter data...'
                row followed by <return> to search. his or her voting record.
                Negative vote polarization leans toward the Democratic party.
                Positive vote polarization leans toward the Republican party.
            """)

            return [ all_votes_header ]

        # This callback updates all votes table
        @app.callback(
            Output(voter_all_votes_table.id, "data"),
            Output(voter_all_votes_table.id, "columns"),
            Input(all_voters_table.id, "derived_virtual_data"),
            Input(all_voters_table.id, "derived_virtual_selected_rows"),
            Input(all_voters_table2.id, "derived_virtual_data"),
            Input(all_voters_table2.id, "derived_virtual_selected_rows"),
            )
        def update_all_votes_table(
            table_rows, derived_virtual_selected_rows,
            table_rows2, derived_virtual_selected_rows2,
            ):
            """Update all votes table."""
            # @TODO: merge this with other update

            callback_data, callback_data2 = process_double_callback(
                table_rows, derived_virtual_selected_rows,
                table_rows2, derived_virtual_selected_rows2,
                )

            if not callback_data:
                return [], []

            if callback_data["party_lean"] == "Democratic":
                party_opposite = "Republican"
            else:
                party_opposite = "Democratic"
            if callback_data2 and callback_data2["party_lean"] == "Democratic":
                party_opposite2 = "Republican"
            else:
                party_opposite2 = "Democratic"

            vote_label = "Vote-1"
            vote_label2 = "Vote-2"
            polarization_label = "Vote-1 polarization"
            polarization_label2 = "Vote-2 polarization"
            vote_polarization_voter = vote_polarization_df.copy()
            vote_polarization_voter["Vote-2"] = "--"
            vote_polarization_voter["Vote-2 polarization"] = "--"

            vote_polarization_voter[vote_label] = vote_polarization_voter.apply(
                lambda row: (voter_bills_dict[callback_data["voter_key"]].get(
                    row["Key"], "--")), axis=1)
            if callback_data2:
                vote_polarization_voter[vote_label2] = vote_polarization_voter.apply(
                    lambda row: (voter_bills_dict[callback_data2["voter_key"]].get(
                        row["Key"], "--")), axis=1)

            vote_polarization_voter = vote_polarization_voter[
                (vote_polarization_voter[vote_label] != "--")
                | (vote_polarization_voter[vote_label2] != "--")]

            polarization_bias_dict = {
                "yes": 1.0,
                "no": -1.0,
                "other": 0.0,
                "--": 0.0,
            }
            vote_polarization_voter[polarization_label] = vote_polarization_voter.apply(
                lambda row: row["Yes polarization"] * polarization_bias_dict[row[vote_label]], axis=1)
            vote_polarization_voter[polarization_label2] = vote_polarization_voter.apply(
                lambda row: row["Yes polarization"] * polarization_bias_dict[row[vote_label2]], axis=1)
            # vote_polarization_voter["Vote polarization"] = vote_polarization_voter["Yes polarization"]
            voter_all_votes_table.empty = False
            voter_all_votes_table.df = vote_polarization_voter
            voter_all_votes_table.update_table_data()
            return voter_all_votes_table.data, voter_all_votes_table.columns

        # These callback updates the first independent vote table
        @app.callback(
            Output('independent_votes1', "children"),
            Input(all_voters_table.id, "derived_virtual_data"),
            Input(all_voters_table.id, "derived_virtual_selected_rows"))
        def update_independent_votes1(table_rows, derived_virtual_selected_rows):
            return update_independent_votes(table_rows, derived_virtual_selected_rows)

        # These callback updates the first independent vote table
        @app.callback(
            Output('independent_votes2', "children"),
            Input(all_voters_table2.id, "derived_virtual_data"),
            Input(all_voters_table2.id, "derived_virtual_selected_rows"))
        def update_independent_votes2(table_rows, derived_virtual_selected_rows):
            return update_independent_votes(table_rows, derived_virtual_selected_rows)


        def update_independent_votes(table_rows, derived_virtual_selected_rows):
            """Update independent votes table."""
            if not derived_virtual_selected_rows:
                return html.Div()

            callback_data = process_all_voters_table_callback(
                pd.DataFrame(table_rows), derived_virtual_selected_rows)

            if callback_data["party_lean"] == "Democratic":
                bill_heap = voter_bills_heap_export[callback_data["voter_key"]]["max_heap"]
                party_opposite = "Republican"
                all_vote_sort_ascending = False
            else:
                bill_heap = voter_bills_heap_export[callback_data["voter_key"]]["min_heap"]
                party_opposite = "Democratic"
                all_vote_sort_ascending = True

            data = []
            for polarization, bill in bill_heap:
                row = bill_lookup[bill]
                row["Vote"] = voter_bills_dict[callback_data["voter_key"]][row["Key"]]
                row["Vote polarization"] = polarization
                data.append(row)
            independent_df = pd.DataFrame.from_dict(data)
            independent_df["Vote"] = independent_df.apply(
                lambda row: voter_bills_dict[callback_data["voter_key"]][row["Key"]], axis=1)
            independent_df = independent_df[independent_table_columns]
            independent_table = SimpleDashTable(
                independent_df, table_style,
                delete_columns=[
                    "Party", "Unanimity", "Yes polarization", "Session", "Key"],
                column_order = independent_table_columns,
                column_name_transform=(
                    lambda value: column_name_transform(value, mobile=mobile)),
                column_specs = default_column_specs,
            )

            def vote_polarization(row):
                vote = row["Vote"]
                if vote == "yes":
                    return row["Party polarization"]
                elif vote == "no":
                    return - row["Party polarization"]
                else:
                    return 0

            if (callback_data["table_row"][callback_data["party_column"]] == "Democratic"
                or callback_data["table_row"][callback_data["party_column"]] == "Republican"):
                    independent_header = dcc.Markdown(f"""
                        ### Independent or bipartisan votes for {callback_data["full_name_and_city"]}
                        Bills where {callback_data["full_name_and_city"]}, a
                        member of the {callback_data["table_row"][callback_data["party_column"]]} party,
                        voted more closely with the {party_opposite} party.
                        Negative vote polarization leans toward the Democratic party.
                        Positive vote polarization leans toward the Republican party.
                        """
                        # f" vpv columns: {str(vote_polarization_voter.columns)}"
                    )
                        # {str(independent_df.columns)}
            else:
                # bill_key = independent_df.at[0,"Key"]
                independent_header = dcc.Markdown(f"""
                    ### Independent or bipartisan votes for {callback_data["full_name_and_city"]}
                    Bills where {callback_data["full_name_and_city"]}, who
                    identifies with the {callback_data["table_row"][callback_data["party_column"]]} party
                    and generally votes with the {callback_data["party_lean"]} party
                    voted more closely with the {party_opposite} party.
                    Negative vote polarization leans toward the Democratic party.
                    Positive vote polarization leans toward the Republican party.
                    """
                    # f" independent_df.columns: {sorted(independent_df.columns)}"
                    # f" independent_table_columns: {sorted(independent_table_columns)}"
                    )
            return[html.Div([
                independent_header,
                independent_table.static_table,
                html.Br(),
                # all_voter_votes_header,
                # full_vote_table.sortable_table,
            ])]

        # execute
        inline = False
        if not prod_mode:
            if inline:
                app.run_server(mode='inline', port=dash_port)
            else:
                app.run_server(port=dash_port)
        else:
            return app

app = run_dash(port=None, mobile=True)
server = app.server

if __name__ == "__main__":
    app.run_server(port=8052)
