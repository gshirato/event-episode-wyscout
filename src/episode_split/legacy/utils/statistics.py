import pandas as pd


def sort_stats(df):
    grouped = df.groupby("team_name")
    stats_df = grouped[["team_name", "dist"]].apply(calc_mean_sd)
    sorted_stats_df = stats_df.sort_values("mean")
    sorted_countries = list(map(lambda x: x[0], sorted_stats_df.index))
    return df.set_index("team_name").loc[sorted_countries].reset_index()


def calc_mean_sd(group):
    # Calculate mean and standard deviation for numeric columns
    mean = group.select_dtypes(include=["number"]).mean()
    sd = group.select_dtypes(include=["number"]).std()

    # Combine mean and sd into a single DataFrame
    result = pd.DataFrame({"mean": mean, "sd": sd})
    return result
