# Logistic Regression
library(lubridate)
library(dplyr)
library(nnet)

# Importing the dataset
dataset = read.csv('earnings_data.csv')
dataset$quarter = as.Date(dataset$quarter, "%m/%d/%Y")

# Splitting the dataset into the Training set and Test set
train = dataset %>%
  filter(quarter < as.Date('2018-03-31'))
train = train[3:ncol(dataset)]

test = dataset %>%
  filter(quarter >= as.Date('2018-03-31')) %>%
  filter(quarter < as.Date('2018-05-31'))
test = test[3:ncol(dataset)]

valid = dataset %>%
  filter(quarter >= as.Date('2018-05-31'))
valid = valid[3:ncol(dataset)]


# Fitting Multinomial Logistic Regression to the Training set
classifier = multinom(return_factor ~ ., data = train)

# Predicting the Test set results
prob_pred = predict(classifier, test, "probs")
y_pred = ifelse(prob_pred > 0.7, 1, 0)

# Making the Confusion Matrix
cm = table(test_set[, 3], y_pred > 0.5)


# define model grid for best subset regression
# defines which predictors are on/off; all combinations presented
model.grid = function(n){
  n.list = rep(list(0:1), n)
  expand.grid(n.list)
}
# function for best subset regression
# ranks predictor combos using 5 selection criteria

best.subset <- function(y, x.vars, data){
  # y       character string and name of dependent variable
  # xvars   character vector with names of predictors
  # data    training data with y and xvar observations
  
  require(dplyr)
  require(purrr)
  require(magrittr)
  
  length(x.vars) %>%
    model.grid %>%
    apply(1, function(x) which(x > 0, arr.ind = TRUE)) %>%
    map(function(x) x.vars[x]) %>%
    .[2:dim(model.grid(length(x.vars)))[1]] %>%
    map(function(x) multinom(paste0(y, " ~ ", paste(x, collapse = "+")), data = data)) %>%
    map(function(x) CV(x)) %>%
    do.call(rbind, .) %>%
    cbind(model.grid(length(x.vars))[-1, ], .) %>%
    arrange(., AICc)
}

y = 'return_factor'
x.vars = c('X1Year','X1month','X3month','X6month',
          'current_ratio',
          'total_debt_equity_ratio',
          'day_sales_outstanding',
          'total_liabilities_total_assets',
          'gross_margin',
          'operating_margin',
          'interest_coverage_ratio',
          'net_profit_margin',
          'roe',
          'changeInCash',
          'changeToLiabilities',
          'changeToNetincome',
          'changeToOperatingActivities')

out = best.subset(y, x.vars, train)
