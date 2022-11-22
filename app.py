import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime


def get_data():
    df: pd.DataFrame = pd.read_csv("./data/results.csv")
    df = df.drop(["neutral", "city"], axis=1)

    df = df[(~df.home_score.isna()) | (~df.away_score.isna())]
    df.home_score = df.home_score.astype(int)
    df.away_score = df.away_score.astype(int)

    return df


def get_result_text(w, l, d):
    if w == 1:
        r = "win"
    elif l == 1:
        r = "defeat"
    else:
        r = "draw"

    return r


def get_results(df, team):
    df["selected_team"] = team
    df["wins"] = np.where(
        (
            (df.home_score > df.away_score) & (df.home_team == team)
            | (df.home_score < df.away_score) & (df.away_team == team)
        ),
        1,
        0,
    )

    df["draws"] = np.where(
        (
            (df.home_score == df.away_score) & (df.home_team == team)
            | (df.home_score == df.away_score) & (df.away_team == team)
        ),
        1,
        0,
    )

    df["defeats"] = np.where(
        (
            (df.home_score < df.away_score) & (df.home_team == team)
            | (df.home_score > df.away_score) & (df.away_team == team)
        ),
        1,
        0,
    )

    df["goals_scored"] = np.where(
        (df.home_team == team), df["home_score"], df["away_score"]
    )

    df["goals_conceded"] = np.where(
        (df.home_team == team), df["away_score"], df["home_score"]
    )

    df["goals_diff"] = df.goals_scored - df.goals_conceded

    df["results"] = df.apply(
        lambda x: get_result_text(x.wins, x.defeats, x.draws), axis=1
    )

    return df


def create_sidebar(teams, df):
    with st.sidebar:
        # Only df where the world cup teams took part in
        df = df[df["home_team"].isin(teams) | df["away_team"].isin(teams)]

        team = st.selectbox("Countries", teams)

        team_cond = (df["home_team"] == team) | (df["away_team"] == team)

        df = df[team_cond]

        # Only df where the chosen team took part in

        tournaments = df.tournament.sort_values().unique()

        trnmt = st.multiselect("Tournaments", tournaments)
        trnmt_cond = df.tournament.isin(trnmt)

        # Only df from the chosen tournaments
        df = df[trnmt_cond] if trnmt else df

        df.date = df.date.apply(lambda d: datetime.strptime(d, "%Y-%m-%d").date())

        min_dt = df.date.min()
        max_dt = df.date.max()

        # Only matches within the selected range of dates
        start_date = st.date_input(
            "Start Date", min_value=min_dt, max_value=max_dt, value=min_dt
        )

        end_date = st.date_input(
            "End Date", min_value=min_dt, max_value=max_dt, value=max_dt
        )

        df = df[(df.date >= start_date) & (df.date <= end_date)].sort_values(
            by="date", ascending=False
        )

        # Top N df from the selected input
        n_matches = st.number_input(
            "Number of matches",
            min_value=1,
            max_value=len(df),
            value=10,
            help="This will limit the number of rows on the dataset",
        )

        return df.head(n_matches), team


def main():

    st.title("FIFA 2022 Qatar Worldcup Teams Analysis")

    wc_teams: list = [
        "Qatar",
        "Ecuador",
        "Senegal",
        "Netherlands",
        "England",
        "Iran",
        "United States",
        "Wales",
        "Argentina",
        "Saudi Arabia",
        "Mexico",
        "Poland",
        "France",
        "Australia",
        "Denmark",
        "Tunisia",
        "Spain",
        "Costa Rica",
        "Germany",
        "Japan",
        "Belgium",
        "Canada",
        "Morocco",
        "Croatia",
        "Brazil",
        "Serbia",
        "Switzerland",
        "Cameroon",
        "Portugal",
        "Ghana",
        "Uruguay",
        "South Korea",
    ]
    wc_teams.sort()

    df = get_data()

    matches, team = create_sidebar(wc_teams, df)

    st.dataframe(matches)

    matches = get_results(matches, team)
    team_results = matches.groupby(by="selected_team", as_index=False)[
        ["wins", "defeats", "draws", "goals_scored", "goals_conceded", "goals_diff"]
    ].sum()

    st.markdown(f"### Latest {team} results")
    st.markdown(
        f"""* {team} has <code style='color:#66cd00'>won</code> **{team_results['wins'][0]}**,
        <code style='color:Yellow'>tied</code> **{team_results['draws'][0]}**
        and <code style='color:#e34234'>lost</code> **{team_results['defeats'][0]}** of its last **{len(matches)}** games""",
        unsafe_allow_html=True,
    )

    cond_color = (
        "<code style='color:#66cd00'>"
        if team_results["goals_diff"][0] > 0
        else "<code style='color:#e34234'>"
    )

    st.markdown(
        f"""* {team} has scored <code style='color:#66cd00'>{team_results['goals_scored'][0]}</code> goals
        and conceded <code style='color:#e34234'>**{team_results['goals_conceded'][0]}**</code> goals
        making up a difference of {cond_color}**{team_results['goals_diff'][0]}**</code> goals""",
        unsafe_allow_html=True,
    )

    bar_plot = px.bar(
        matches, x="results", color="results", title="Distribution of match results"
    )
    line_plot = px.line(
        matches, x="date", y="goals_scored", title="Goals scored distribution over time"
    )
    bar_plot.update_xaxes(showgrid=False)
    bar_plot.update_yaxes(showgrid=False)

    st.plotly_chart(bar_plot)
    st.plotly_chart(line_plot)

    print(matches)


if __name__ == "__main__":
    main()
