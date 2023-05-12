packages <- c("tidyverse", "elo", "formattable", "lubridate", "showtext")
install.packages(setdiff(packages, rownames(installed.packages())))

library(tidyverse)
library(formattable)
library(elo)
library(lubridate)
library(showtext)


match_results <- read_csv("../data/results.csv")
match_results %>% glimpse
match_results_wrangled <- match_results %>% 

  # Rename United States and South Korea to USA and Korea Republic respectively to reflect current naming. We need to do this to both 'home_team' and 'away_team' columns
  mutate(home_team = case_when(home_team == "United States" ~ "USA",
                               home_team == "South Korea" ~ "Korea Republic",
                               TRUE ~ home_team),
         away_team = case_when(away_team == "United States" ~ "USA",
                               away_team == "South Korea" ~ "Korea Republic",
                               TRUE ~ away_team),

         # Add a new column for match result from both the home team and away team's perspectives. 1 = Win, 0.5 = Draw, 0 = Loss.
         home_result = case_when(home_score > away_score ~ 1,
                                 home_score < away_score ~ 0,
                                 home_score == away_score ~ 0.5),
         away_result = case_when(home_score < away_score ~ 1,
                                 home_score > away_score ~ 0,
                                 home_score == away_score ~ 0.5),

         # Add a margin feature
         margin = abs(home_score - away_score)) %>% 

  # If there are any matches missing score data, we don't want to use them for our Elo model - drop any data where we are missing a match margin
  drop_na(margin)



final_dataset <- match_results_wrangled %>% 

  # Add a column to show 100 where there is a home ground advantage or 0 when played at a neutral venue. Our Elo model will call on this column for HGA.
  mutate(hga = 100*!neutral,

         # Allocate each tournament within the data to a K-weighting according to the above definition. Note that this section is quite open to interpretation.
         tournament_weight = case_when(tournament == "FIFA World Cup" ~ 60,
                                       tournament %in% c("Confederations Cup", "African Cup of Nations", "Copa América", 
                                                         "UEFA Euro", "AFC Asian Cup") ~ 50,
                                       str_detect(tolower(tournament), "qualification") ~ 40,
                                       str_detect(tolower(tournament), " cup") ~ 40,
                                       tournament %in% c("UEFA Nations League", "CONCACAF Nations League") ~ 40,
                                       tournament == "Friendly" ~ 20,
                                       TRUE ~ 30),

         # Use our 'margin' feature to create the goal difference K-multiplier.
         goal_diff_multiplier = case_when(margin <= 1 ~ 1,
                                          margin == 2 ~ 1.5,
                                          margin == 3 ~ 1.75, 
                                          margin >= 4 ~ 1.75 + (margin-3)/8),

         # Combine the tournament weight and goal difference features to obtain our final K value for each match.
         k = tournament_weight*goal_diff_multiplier,

         # Also add a 'match_id' feaature to identify each match by number - we'll use this later.
         match_id = row_number()) %>% 
  relocate(match_id)


elo_model <- elo.run(data = final_dataset,
                     formula = home_result ~ adjust(home_team, hga) + away_team + k(k))


final_elos <- final.elos(elo_model) %>% 
  enframe(name = "team", value = "elo") %>% 
  arrange(desc(elo))


# See the top 10 rated nations
final_elos %>% slice_head(n = 10)
# Load Google fonts from https://fonts.google.com/
font_add_google(name = "Poor Story", family = "poor_story")
showtext_auto()

# Visualise final Elo ratings
final_elos %>% 
  ggplot(aes(x = elo)) +
  geom_histogram(binwidth = 100, fill = "#ffb80c", color = "white") +
  theme_minimal() +
  labs(x = "Elo Rating",
       y = "# of Teams",
       title = "Distribution of Final Elo Ratings") +
  theme(panel.background = element_rect(fill = "transparent", colour = NA),
        plot.background = element_rect(fill = "transparent", colour = NA),
        text = element_text(color = "black", family = "poor_story"),
        axis.text = element_text(color = "black", size = 14),
        plot.title = element_text(color = "black", size = 24, hjust = 0.5),
        axis.title = element_text(family = "poor_story", size = 16),
        plot.margin = unit(c(1,1,1,1), "cm"))


brier(elo_model)
world_cup_matchups <- read_csv("../data/dummy_submission_file.csv")
write.csv(final_elos,"../data/elos.csv")

world_cup_matchups %>% glimpse

# Start by taking our Elo model, wrangling the match-by-match rating updates within the stored model and joining to our historic data set.
elo_results <- elo_model %>% 
  as_tibble() %>% 
  mutate(match_id = row_number()) %>% 
  select(match_id, 
         home_update = update.A,
         away_update = update.B,
         home_elo = elo.A,
         away_elo = elo.B) %>% 

  # Join onto our historic data set using the match_id columns we created as a join key
  right_join(final_dataset, by = "match_id")


write.csv(elo_results,'../data/elo_hist.csv')


draw_rates <- elo_results %>%
  mutate(home_elo_pre_match = home_elo - home_update,
         away_elo_pre_match = away_elo - away_update,
         home_prob = elo.prob(home_elo_pre_match, away_elo_pre_match),
         away_prob = 1 - home_prob,
         prob_diff = abs(home_prob - away_prob),
         prob_diff_bucket = round(20*prob_diff)/20) %>% # Bucket into 20 groups at 5% increments between 0% and 100%
  filter(year(date) >= 2005) %>%  # Filter down to the past 15 years to only bucket matches once some fairly decent Elo ratings have been established
  group_by(prob_diff_bucket) %>%
  summarise(draw_rate = sum(home_result == 0.5)/n())

draw_rates %>% slice_head(n = 10)

draw_rates %>%
  mutate(draw_rate = percent(draw_rate, digits = 0),
         prob_diff_bucket = percent(prob_diff_bucket, digits = 0)) %>%
  ggplot(aes(x = prob_diff_bucket, y = draw_rate)) +
  geom_col(fill = "#ffb80c") +
  geom_text(aes(label = draw_rate, y = draw_rate + 0.01), 
            size = 3.5, family = "poor_story") +
  theme_minimal() +
  scale_y_continuous(labels = scales::percent) +
  scale_x_continuous(labels = scales::percent, breaks = scales::pretty_breaks()) +
  labs(y = "Historic Draw Rate", 
       x = "Difference in Win Probability Between Home & Away Sides",
       title = "Draw Frequency by Heaviness of Favouritism") +
  theme(panel.background = element_rect(fill = "transparent", colour = NA),
        plot.background = element_rect(fill = "transparent", colour = NA),
        text = element_text(color = "black", family = "poor_story"),
        axis.text = element_text(color = "black", size = 12),
        plot.title = element_text(color = "black", size = 24, hjust = 0.5),
        axis.title = element_text(family = "poor_story", size = 16),
        plot.margin = unit(c(1,1,1,1), "cm"))

elo_results %>% 
  select(match_id, date, home_team, home_elo) %>% rename(team = home_team, elo = home_elo) %>% 
  bind_rows(elo_results %>% select(match_id, date, away_team, away_elo) %>% rename(team = away_team, elo = away_elo)) %>% 
  arrange(match_id) %>% 
  filter(team == "Australia") %>% 
  ggplot(aes(x = date, y = elo, group = 1)) +
  geom_hline(yintercept = 1500, linetype = "dashed", color = "black") +
  geom_line(color = "#ffb80c", size = 1) +
  theme_minimal() +
  labs(x = "Year", y = "Elo Rating",
       title = "Australia's Historic Elo Rating") + 
  theme(panel.background = element_rect(fill = "transparent", colour = NA),
        plot.background = element_rect(fill = "transparent", colour = NA),
        text = element_text(color = "black", family = "poor_story"),
        axis.text = element_text(color = "black", size = 12),
        plot.title = element_text(color = "black", size = 24, hjust = 0.5),
        axis.title = element_text(family = "poor_story", size = 16),
        plot.margin = unit(c(1,1,1,1), "cm"))

world_cup_predictions <- world_cup_matchups %>%
  # Join on final home and away team Elo ratings ahead of calculating win probabilities
  left_join(final_elos %>% rename(home_elo = elo), by = c("home_team" = "team")) %>%
  left_join(final_elos %>% rename(away_elo = elo), by = c("away_team" = "team")) %>%

  # Calculate win probabilities
  mutate(home_team_prob = elo.prob(home_elo, away_elo),
         away_team_prob = elo.prob(away_elo, home_elo),

         # Just as we did with finding draw rates, group each match into probability differential buckets so that we can apply the correct draw rate
         prob_diff = abs(home_team_prob - away_team_prob),
         prob_diff_bucket = round(20*prob_diff)/20) %>%

  # Join on our draw rates data frame - this essentially gives us the historic draw rate for the given match-up's probability split
  left_join(draw_rates, by = "prob_diff_bucket") %>%

  # update the draw_prob column accordingly for group stage matches. Set draw_prob to 0 for knockout matches where draws aren't possible.
  mutate(draw_prob = case_when(stage == "Group" ~ draw_rate,
                               stage == "Knockout" ~ 0),

         # Adjust home_team_prob and away_team_prob columns proportionally to allow for draw probability
         home_team_prob = home_team_prob * (1 - draw_prob),
         away_team_prob = away_team_prob * (1 - draw_prob)) %>%

  # Remove redundant columns
  select(home_team:away_team_prob)

# View 5 group stage matches and 5 knockout matches
world_cup_predictions %>% group_by(stage) %>% slice_head(n = 5)
model_name = "Elo_Tutorial"
file_name=paste(model_name,"_submission_file.csv",sep="")
write.csv(world_cup_predictions,file_name)
