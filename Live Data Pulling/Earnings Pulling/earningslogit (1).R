# Logistic Regression
library(lubridate)
library(dplyr)
library(nnet)
library(purrr)
library(magrittr)

# Importing the dataset
dataset = read.csv('earnHist_v3.csv')
dataset$quarter = as.Date(dataset$quarter, "%m/%d/%Y")

# columns = c("X1Year","X1month","industry","current_ratio",'total_debt_equity_ratio',
#             'day_sales_outstanding','gross_margin','operating_margin',
#             'interest_coverage_ratio','net_profit_margin','roe','changeToLiabilities',
#             'changeToNetincome','changeToOperatingActivities','return_factor')

# columns = c("X1Year","X1month","industry","current_ratio",'total_debt_equity_ratio',
#             'day_sales_outstanding','gross_margin','operating_margin',
#             'interest_coverage_ratio','net_profit_margin','roe','changeToLiabilities',
#             'changeToNetincome','changeToOperatingActivities','return_factor')

columns = c("industry","current_ratio","total_debt_equity_ratio",
            "gross_margin","changeToLiabilities","changeToNetincome",
            "changeToOperatingActivities","operating_margin","interest_coverage_ratio",
            "net_profit_margin","X1Year","day_sales_outstanding","roe",'return_factor')


# Splitting the dataset into the Training set and Test set
train = dataset %>%
  filter(quarter < as.Date('2018-04-30'))
train = train[,columns]

test = dataset %>%
  filter(quarter >= as.Date('2018-04-30'))
test = test[,columns]

test_y_actual = data.frame(test$return_factor)

for(level in unique(test_y_actual$test.return_factor)){
  test_y_actual[level] <- ifelse(test_y_actual$test.return_factor == level, 1, 0)
}


# valid = dataset %>%
#   filter(quarter >= as.Date('2018-05-31'))
# valid = valid[,columns]

# define model grid for best subset regression
# defines which predictors are on/off; all combinations presented
model.grid = function(n){
  n.list = rep(list(0:1), n)
  expand.grid(n.list)
}

# function for best subset regression

best_set = length(columns) %>%
  model.grid %>%
  apply(1, function(x) which(x > 0, arr.ind = TRUE)) %>%
  map(function(x) columns[x]) %>%
  .[2:dim(model.grid(length(columns)))[1]]

ests = list()
i = 1
for (set in best_set) {
  curr_reg = multinom(paste0('return_factor', " ~ ", paste(set, collapse = "+")),
                      data = train)
  # Predicting the Test set results
  prob_pred = predict(curr_reg, test, "probs")
  y_pred = ifelse(prob_pred > 0.7, 1, 0)
  
  # Making the Confusion Matrix
  cm = table(unlist(test_y_actual[,c('down','flat','up')]), unlist(y_pred))
  result = tryCatch(
    {cm[2,2]},
    error = function(cond) {
      return(0)
    }
  )
  ests[[i]] = result
  i = i + 1
}

####################################################3

data = dataset[c(unlist(best_set[3709]), 'return_factor','quarter')]

# Splitting the dataset into the Training set and Test set
train = data %>%
  filter(quarter < as.Date('2018-04-30'))
train = train[,c(unlist(best_set[3709]), 'return_factor')]

test = data %>%
  filter(quarter >= as.Date('2018-04-30'))
test = test[,c(unlist(best_set[3709]), 'return_factor')]


# Fitting Multinomial Logistic Regression to the Training set
classifier = multinom(return_factor ~. , 
                      data = train)

stderrors = t(summary(classifier)$standard.errors)

# Predicting the Test set results
prob_pred = predict(classifier, test, "probs")
y_pred = ifelse(prob_pred > 0.5, 1, 0)


# Making the Confusion Matrix
cm = table(unlist(test_y_actual[,c('down','flat','up')]), unlist(y_pred))
correct_ests = cm[2,2]










#######################################################
# define model grid for best subset regression
# defines which predictors are on/off; all combinations presented
model.grid = function(n){
  n.list = rep(list(0:1), n)
  expand.grid(n.list)
}

# function for best subset regression
# ranks predictor combos using 5 selection criteria

best_set = length(columns) %>%
  model.grid %>%
  apply(1, function(x) which(x > 0, arr.ind = TRUE)) %>%
  map(function(x) columns[x]) %>%
  .[2:dim(model.grid(length(columns)))[1]]

ests = list()
i = 1
for (set in best_set[1:5]) {
  curr_reg = multinom(paste0('return_factor', " ~ ", paste(set, collapse = "+")),
                      data = train)
  # Predicting the Test set results
  prob_pred = predict(curr_reg, test, "probs")
  y_pred = ifelse(prob_pred > 0.7, 1, 0)
  
  # Making the Confusion Matrix
  cm = table(unlist(test_y_actual[,c('down','flat','up')]), unlist(y_pred))
  result = tryCatch(
    {cm[2,2]},
    error = function(cond) {
      return(0)
    }
  )
  ests[[i]] = result
  i = i + 1
}

factors = best_set[which(unlist(ests) == max(unlist(ests)))]
top_factors = unique(unlist(factors))

# best.subset = function(y, x.vars, data){
#   # y       character string and name of dependent variable
#   # xvars   character vector with names of predictors
#   # data    training data with y and xvar observations
#   
#   best_sets = length(x.vars) %>%
#     model.grid %>%
#     apply(1, function(x) which(x > 0, arr.ind = TRUE)) %>%
#     map(function(x) x.vars[x]) %>%
#     .[2:dim(model.grid(length(x.vars)))[1]]
#   
#   length(x.vars) %>%
#     model.grid %>%
#     apply(1, function(x) which(x > 0, arr.ind = TRUE)) %>%
#     map(function(x) x.vars[x]) %>%
#     .[2:dim(model.grid(length(x.vars)))[1]] %>%
#     map(function(x) multinom(paste0(y, " ~ ", paste(x, collapse = "+")), data = data)) %>%
#     map(function(x) CV(x)) %>%
#     do.call(rbind, .) %>%
#     cbind(model.grid(length(x.vars))[-1, ], .) %>%
#     arrange(., AICc)
# }

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
