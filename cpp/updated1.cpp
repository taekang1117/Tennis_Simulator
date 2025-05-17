#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <random>
#include <chrono>
#include <numeric>
using namespace std;

struct PlayerStats {
    double DR;
    double A_percent;
    double DF_percent;
    double FirstIn;
    double FirstPercent;
    double SecondPercent;
    double TW_percent; // True Win percentage
    int result; // New
};

struct MatchData {
    vector<double> features;  // Combined features of both players
    double result;            // 1 if player A won, 0 if player B won
};

// Function to calculate Wsp score with the original formula
double calculate_Wsp(const PlayerStats& p) {
    double A = p.A_percent / 100.0;
    double DF = p.DF_percent / 100.0;
    double FirstIn = p.FirstIn / 100.0;
    double FirstPercent = p.FirstPercent / 100.0;
    double SecondPercent = p.SecondPercent / 100.0;

    double Wa = A;
    double Wdf = DF * (-3);
    double W1st = (FirstIn - A) * FirstPercent * 4;
    double W2nd = (1 - FirstIn - DF) * SecondPercent * 2.5;
    double Wsp = (Wa) + (Wdf) + (W1st) + (W2nd);

    return Wsp;
}

// Function to calculate Adjusted Ratio (AR)
double calculate_AR(const PlayerStats& p) {
    double Wsp = calculate_Wsp(p);
    double TW = p.TW_percent / 100.0; // Convert percentage to decimal
    
    // Convert Wsp to win probability using sigmoid function
    double Wsp_prob = 1.0 / (1.0 + exp(-Wsp));
    
    // Calculate AR such that AR * Wsp_prob = TW
    // If Wsp_prob is very small, cap the AR to avoid extreme values
    if (fabs(Wsp_prob) < 0.01) {
        return TW / 0.01;
    }
    
    return TW / Wsp_prob;
}

// Function to calculate adjusted Wsp score using AR
double calculate_adjusted_Wsp(const PlayerStats& p, double ar) {
    double original_Wsp = calculate_Wsp(p);
    return original_Wsp * ar;
}

class LinearModel {
private:
    vector<double> weights;
    double bias;
    double learning_rate;
    int iterations;

public:
    LinearModel(int feature_count, double lr = 0.01, int iters = 1000) 
        : learning_rate(lr), iterations(iters) {
        // Initialize weights with small random values
        unsigned seed = chrono::system_clock::now().time_since_epoch().count();
        default_random_engine generator(seed);
        normal_distribution<double> distribution(0.0, 0.1);
        
        weights.resize(feature_count);
        for (int i = 0; i < feature_count; i++) {
            weights[i] = distribution(generator);
        }
        bias = distribution(generator);
    }

    double predict(const vector<double>& features) const {
        double result = bias;
        for (size_t i = 0; i < weights.size(); i++) {
            result += weights[i] * features[i];
        }
        // Apply sigmoid to get probability
        return 1.0 / (1.0 + exp(-result));
    }

    void train(const vector<MatchData>& training_data) {
        cout << "Training linear model with " << training_data.size() << " matches...\n";
        
        for (int iter = 0; iter < iterations; iter++) {
            double total_loss = 0.0;
            
            // Gradient accumulators
            vector<double> weight_gradients(weights.size(), 0.0);
            double bias_gradient = 0.0;
            
            for (const auto& match : training_data) {
                // Forward pass (prediction)
                double prediction = predict(match.features);
                
                // Compute error
                double error = prediction - match.result;
                total_loss += error * error;  // squared error
                
                // Update gradients
                for (size_t i = 0; i < weights.size(); i++) {
                    weight_gradients[i] += error * match.features[i];
                }
                bias_gradient += error;
            }
            
            // Apply gradients
            for (size_t i = 0; i < weights.size(); i++) {
                weights[i] -= learning_rate * weight_gradients[i] / training_data.size();
            }
            bias -= learning_rate * bias_gradient / training_data.size();
            
            // Print progress occasionally
            if ((iter + 1) % 100 == 0 || iter == 0) {
                cout << "Iteration " << (iter + 1) << ", Loss: " 
                     << (total_loss / training_data.size()) << endl;
            }
        }
        
        // Print final weights
        cout << "\nTrained model weights:\n";
        cout << "Bias: " << bias << endl;
        cout << "DR difference: " << weights[0] << endl;
        cout << "Ace % difference: " << weights[1] << endl;
        cout << "DF % difference: " << weights[2] << endl;
        cout << "First serve % difference: " << weights[3] << endl;
        cout << "First serve win % difference: " << weights[4] << endl;
        cout << "Second serve win % difference: " << weights[5] << endl;
        cout << endl;
    }
    
    // Calculate feature importance (absolute value of weights)
    vector<pair<string, double>> get_feature_importance() const {
        vector<string> feature_names = {
            "DR difference", 
            "Ace % difference", 
            "DF % difference", 
            "First serve % difference", 
            "First serve win % difference", 
            "Second serve win % difference"
        };
        
        vector<pair<string, double>> importance;
        for (size_t i = 0; i < weights.size(); i++) {
            importance.push_back({feature_names[i], fabs(weights[i])});
        }
        
        // Sort by importance (descending)
        sort(importance.begin(), importance.end(), 
             [](const pair<string, double>& a, const pair<string, double>& b) {
                 return a.second > b.second;
             });
             
        return importance;
    }
};

// Function to calculate median of a vector
double calculate_median(vector<double> values) {
    size_t size = values.size();
    if (size == 0) {
        return 0; // Return 0 for empty vector
    }
    
    sort(values.begin(), values.end());
    
    if (size % 2 == 0) {
        // If even number of elements, average the middle two
        return (values[size / 2 - 1] + values[size / 2]) / 2;
    } else {
        // If odd number of elements, return the middle one
        return values[size / 2];
    }
}

// Function to calculate average of a vector
double calculate_average(const vector<double>& values) {
    if (values.empty()) return 0;
    double sum = 0;
    for (double value : values) {
        sum += value;
    }
    return sum / values.size();
}

// Function to parse a CSV file and load all player stats as a vector
/*
vector<PlayerStats> load_all_player_stats(const string& filename) {
    ifstream file(filename);
    string line;
    vector<PlayerStats> all_stats;

    if (!file.is_open()) {
        cerr << "Error opening file: " << filename << endl;
        exit(1);
    }

    // Skip header
    getline(file, line);

    // Read all lines of data
    while (getline(file, line)) {
        stringstream ss(line);
        string value;
        PlayerStats stats;

        if (getline(ss, value, ',')) stats.DR = stod(value);
        if (getline(ss, value, ',')) stats.A_percent = stod(value);
        if (getline(ss, value, ',')) stats.DF_percent = stod(value);
        if (getline(ss, value, ',')) stats.FirstIn = stod(value);
        if (getline(ss, value, ',')) stats.FirstPercent = stod(value);
        if (getline(ss, value, ',')) stats.SecondPercent = stod(value);
        if (getline(ss, value, ',')) stats.TW_percent = stod(value);
        
        all_stats.push_back(stats);
    }

    return all_stats;
} 
*/

vector<PlayerStats> load_all_player_stats(const string& filename) {
    ifstream file(filename);
    string line;
    vector<PlayerStats> all_stats;

    if (!file.is_open()) {
        cerr << "Error opening file: " << filename << endl;
        exit(1);
    }

    // Skip header
    getline(file, line);

    while (getline(file, line)) {
        stringstream ss(line);
        string value;
        PlayerStats stats;

        getline(ss, value, ','); stats.DR           = stod(value);
        getline(ss, value, ','); stats.A_percent    = stod(value);
        getline(ss, value, ','); stats.DF_percent   = stod(value);
        getline(ss, value, ','); stats.FirstIn      = stod(value);
        getline(ss, value, ','); stats.FirstPercent = stod(value);
        getline(ss, value, ','); stats.SecondPercent= stod(value);
        getline(ss, value, ','); stats.TW_percent   = stod(value);

        // *** NEW: try to read a Result column; default to -1 if missing ***
        if (getline(ss, value, ',')) {
            stats.result = stoi(value);
        } else {
            stats.result = -1;
        }

        all_stats.push_back(stats);
    }

    return all_stats;
}


// Function to load aggregated player stats
PlayerStats load_player_stats(const string& filename, bool use_median = true) {
    vector<PlayerStats> all_stats = load_all_player_stats(filename);
    
    // Vectors to store all values
    vector<double> DR_values;
    vector<double> A_percent_values;
    vector<double> DF_percent_values;
    vector<double> FirstIn_values;
    vector<double> FirstPercent_values;
    vector<double> SecondPercent_values;
    vector<double> TW_percent_values;
    
    // Extract values into separate vectors
    for (const auto& stats : all_stats) {
        DR_values.push_back(stats.DR);
        A_percent_values.push_back(stats.A_percent);
        DF_percent_values.push_back(stats.DF_percent);
        FirstIn_values.push_back(stats.FirstIn);
        FirstPercent_values.push_back(stats.FirstPercent);
        SecondPercent_values.push_back(stats.SecondPercent);
        TW_percent_values.push_back(stats.TW_percent);
    }

    PlayerStats stats;
    
    // Calculate median or average values based on the parameter
    if (use_median) {
        stats.DR = calculate_median(DR_values);
        stats.A_percent = calculate_median(A_percent_values);
        stats.DF_percent = calculate_median(DF_percent_values);
        stats.FirstIn = calculate_median(FirstIn_values);
        stats.FirstPercent = calculate_median(FirstPercent_values);
        stats.SecondPercent = calculate_median(SecondPercent_values);
        stats.TW_percent = calculate_median(TW_percent_values);
    } else {
        stats.DR = calculate_average(DR_values);
        stats.A_percent = calculate_average(A_percent_values);
        stats.DF_percent = calculate_average(DF_percent_values);
        stats.FirstIn = calculate_average(FirstIn_values);
        stats.FirstPercent = calculate_average(FirstPercent_values);
        stats.SecondPercent = calculate_average(SecondPercent_values);
        stats.TW_percent = calculate_average(TW_percent_values);
    }

    return stats;
}

// Generate feature vector from two players' stats
vector<double> generate_features(const PlayerStats& playerA, const PlayerStats& playerB) {
    vector<double> features = {
        playerA.DR - playerB.DR,
        playerA.A_percent - playerB.A_percent,
        playerA.DF_percent - playerB.DF_percent,
        playerA.FirstIn - playerB.FirstIn,
        playerA.FirstPercent - playerB.FirstPercent,
        playerA.SecondPercent - playerB.SecondPercent
    };
    return features;
}

vector<MatchData> generate_real_training_data(const vector<PlayerStats>& player1_stats, 
    const vector<PlayerStats>& player2_stats,
    int num_augmented_samples = 1000) {
vector<MatchData> training_data;
unsigned seed = chrono::system_clock::now().time_since_epoch().count();
default_random_engine generator(seed);

// First, create match data from player stats with actual results
for (const auto& p1_stat : player1_stats) {
// Skip entries without a valid result
if (p1_stat.result < 0) continue;

MatchData match;

// We need to compare with a hypothetical opponent
// Use the median of player2_stats for consistency
PlayerStats median_p2;
vector<double> DR_values, A_percent_values, DF_percent_values, 
FirstIn_values, FirstPercent_values, SecondPercent_values;

for (const auto& p2_stat : player2_stats) {
DR_values.push_back(p2_stat.DR);
A_percent_values.push_back(p2_stat.A_percent);
DF_percent_values.push_back(p2_stat.DF_percent);
FirstIn_values.push_back(p2_stat.FirstIn);
FirstPercent_values.push_back(p2_stat.FirstPercent);
SecondPercent_values.push_back(p2_stat.SecondPercent);
}

median_p2.DR = calculate_median(DR_values);
median_p2.A_percent = calculate_median(A_percent_values);
median_p2.DF_percent = calculate_median(DF_percent_values);
median_p2.FirstIn = calculate_median(FirstIn_values);
median_p2.FirstPercent = calculate_median(FirstPercent_values);
median_p2.SecondPercent = calculate_median(SecondPercent_values);

// Generate features (differences between player1 and median player2)
match.features = generate_features(p1_stat, median_p2);

// Use the actual result (1 = win, 0 = loss)
match.result = p1_stat.result;

training_data.push_back(match);
}

// Do the same for player2 stats
for (const auto& p2_stat : player2_stats) {
// Skip entries without a valid result
if (p2_stat.result < 0) continue;

MatchData match;

// Create median player1 for comparison
PlayerStats median_p1;
vector<double> DR_values, A_percent_values, DF_percent_values, 
FirstIn_values, FirstPercent_values, SecondPercent_values;

for (const auto& p1_stat : player1_stats) {
DR_values.push_back(p1_stat.DR);
A_percent_values.push_back(p1_stat.A_percent);
DF_percent_values.push_back(p1_stat.DF_percent);
FirstIn_values.push_back(p1_stat.FirstIn);
FirstPercent_values.push_back(p1_stat.FirstPercent);
SecondPercent_values.push_back(p1_stat.SecondPercent);
}

median_p1.DR = calculate_median(DR_values);
median_p1.A_percent = calculate_median(A_percent_values);
median_p1.DF_percent = calculate_median(DF_percent_values);
median_p1.FirstIn = calculate_median(FirstIn_values);
median_p1.FirstPercent = calculate_median(FirstPercent_values);
median_p1.SecondPercent = calculate_median(SecondPercent_values);

// Generate features (median player1 vs player2)
// Note: we're flipping the order so that a p2_stat result of 1 means player2 wins
match.features = generate_features(median_p1, p2_stat);

// We need to flip the result since we're treating player2 as "playerA" in this comparison
// If player2's result is 1 (win), then player1 would lose, so result is 0
match.result = 1.0 - p2_stat.result; 

training_data.push_back(match);
}

// Calculate the number of real match data samples
size_t real_samples = training_data.size();
cout << "Generated " << real_samples << " training samples from real match results." << endl;

// If there are no real samples, return empty training data
if (real_samples == 0) {
cout << "Warning: No valid results found in the data. Cannot generate training samples." << endl;
return training_data;
}

// If requested, augment with additional samples
if (num_augmented_samples > 0) {
// Calculate mean and std dev for each feature in real data
vector<double> feature_means(6, 0.0);
vector<double> feature_stddevs(6, 0.0);

// Calculate means
for (const auto& match : training_data) {
for (size_t i = 0; i < 6; i++) {
feature_means[i] += match.features[i];
}
}

for (size_t i = 0; i < 6; i++) {
feature_means[i] /= real_samples;
}

// Calculate standard deviations
for (const auto& match : training_data) {
for (size_t i = 0; i < 6; i++) {
feature_stddevs[i] += pow(match.features[i] - feature_means[i], 2);
}
}

for (size_t i = 0; i < 6; i++) {
feature_stddevs[i] = sqrt(feature_stddevs[i] / real_samples);
// Avoid zero std dev
if (feature_stddevs[i] < 0.0001) {
feature_stddevs[i] = 0.0001;
}
}

// Now generate augmented samples based on the real data distribution
// Create a logistic regression model on the real data to predict outcomes for synthetic data
LinearModel temp_model(6, 0.01, 1000);
temp_model.train(training_data);

for (int i = 0; i < num_augmented_samples; i++) {
MatchData match;
match.features.resize(6);

// Generate features using normal distributions based on real data
for (size_t j = 0; j < 6; j++) {
normal_distribution<double> feature_dist(feature_means[j], feature_stddevs[j]);
match.features[j] = feature_dist(generator);
}

// Use our trained model to predict the result
// This maintains the relationship between features and outcome based on real data
double win_prob = temp_model.predict(match.features);

// Convert probability to binary outcome with some randomness
bernoulli_distribution binary_dist(win_prob);
match.result = binary_dist(generator) ? 1.0 : 0.0;

training_data.push_back(match);
}

cout << "Added " << num_augmented_samples << " augmented samples based on real data patterns." << endl;
}

return training_data;
}

// Function to evaluate model on real data
void evaluate_model(const LinearModel& model, const vector<MatchData>& test_data) {
    double total_loss = 0.0;
    int correct_predictions = 0;
    
    for (const auto& match : test_data) {
        double prediction = model.predict(match.features);
        
        // For squared error loss
        total_loss += pow(prediction - match.result, 2);
        
        // For accuracy (threshold at 0.5)
        bool predicted_win = (prediction >= 0.5);
        bool actual_win = (match.result >= 0.5);
        if (predicted_win == actual_win) {
            correct_predictions++;
        }
    }
    
    double mse = total_loss / test_data.size();
    double accuracy = 100.0 * correct_predictions / test_data.size();
    
    cout << "Model Evaluation:" << endl;
    cout << "Mean Squared Error: " << mse << endl;
    cout << "Accuracy: " << accuracy << "%" << endl;
}

void print_player_stats(const PlayerStats& stats, const string& player_name) {
    cout << "--- " << player_name << " Stats Summary ---\n";
    cout << "DR: " << stats.DR << endl;
    cout << "Ace %: " << stats.A_percent << "%" << endl;
    cout << "Double Fault %: " << stats.DF_percent << "%" << endl;
    cout << "First Serve In %: " << stats.FirstIn << "%" << endl;
    cout << "First Serve Win %: " << stats.FirstPercent << "%" << endl;
    cout << "Second Serve Win %: " << stats.SecondPercent << "%" << endl;
    cout << "True Win %: " << stats.TW_percent << "%" << endl;
    cout << endl;
}

// Function to calculate optimal AR coefficient using regression
double calculate_optimal_AR_coefficient(const vector<PlayerStats>& all_stats) {
    // Prepare X and Y data for linear regression
    // X = original win probability from Wsp, Y = true win percentage
    vector<double> X_vals;
    vector<double> Y_vals;
    
    for (const auto& stats : all_stats) {
        double Wsp = calculate_Wsp(stats);
        double win_prob = 1.0 / (1.0 + exp(-Wsp)); // Convert Wsp to probability
        X_vals.push_back(win_prob);
        Y_vals.push_back(stats.TW_percent / 100.0); // Convert percentage to decimal
    }
    
    // Simple linear regression to find the coefficient
    // We want to find coefficient k such that Y = k*X
    // The optimal k = sum(X*Y) / sum(X^2)
    double sum_XY = 0.0;
    double sum_X2 = 0.0;
    
    for (size_t i = 0; i < X_vals.size(); i++) {
        sum_XY += X_vals[i] * Y_vals[i];
        sum_X2 += X_vals[i] * X_vals[i];
    }
    
    // Avoid division by zero
    if (sum_X2 < 0.0001) {
        return 1.0; // Default to 1 if we can't calculate
    }
    
    return sum_XY / sum_X2;
}

// Function to perform k-fold cross-validation
void perform_cross_validation(const vector<MatchData>& all_data, int k = 5) {
    // Shuffle the data
    vector<MatchData> shuffled_data = all_data;
    unsigned seed = chrono::system_clock::now().time_since_epoch().count();
    shuffle(shuffled_data.begin(), shuffled_data.end(), default_random_engine(seed));
    
    int fold_size = shuffled_data.size() / k;
    vector<double> fold_accuracies;
    
    cout << "\n--- Performing " << k << "-fold cross-validation ---\n";
    
    for (int i = 0; i < k; i++) {
        // Prepare train and test sets
        vector<MatchData> test_data;
        vector<MatchData> train_data;
        
        for (int j = 0; j < (int)shuffled_data.size(); j++) {
            if (j >= i * fold_size && j < (i + 1) * fold_size) {
                test_data.push_back(shuffled_data[j]);
            } else {
                train_data.push_back(shuffled_data[j]);
            }
        }
        
        // Train model
        LinearModel model(6, 0.1, 500); // Shorter training for CV
        model.train(train_data);
        
        // Evaluate
        double total_loss = 0.0;
        int correct_predictions = 0;
        
        for (const auto& match : test_data) {
            double prediction = model.predict(match.features);
            
            // For accuracy (threshold at 0.5)
            bool predicted_win = (prediction >= 0.5);
            bool actual_win = (match.result >= 0.5);
            if (predicted_win == actual_win) {
                correct_predictions++;
            }
        }
        
        double accuracy = 100.0 * correct_predictions / test_data.size();
        fold_accuracies.push_back(accuracy);
        
        cout << "Fold " << (i + 1) << " Accuracy: " << accuracy << "%" << endl;
    }
    
    // Calculate average accuracy
    double avg_accuracy = accumulate(fold_accuracies.begin(), fold_accuracies.end(), 0.0) / k;
    cout << "Average Cross-Validation Accuracy: " << avg_accuracy << "%" << endl;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <Player1 CSV file> <Player2 CSV file> [options]\n";
        cerr << "Options:\n";
        cerr << "  --avg       Use average instead of median (default is median)\n";
        cerr << "  --classic   Use classic formula only\n";
        cerr << "  --ml        Use machine learning model only\n";
        cerr << "  --both      Use both classic and ML models (default)\n";
        cerr << "  --noar      Skip using Adjusted Ratio\n";
        cerr << "  --cross-val Perform cross-validation\n";
        return 1;
    }

    string player1_file = argv[1];
    string player2_file = argv[2];
    
    // Default options
    bool use_median = true;
    bool use_classic = true;
    bool use_ml = true;
    bool use_ar = true;
    bool perform_cv = false;
    
    // Parse additional arguments
    for (int i = 3; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--avg") {
            use_median = false;
        } else if (arg == "--classic") {
            use_classic = true;
            use_ml = false;
        } else if (arg == "--ml") {
            use_classic = false;
            use_ml = true;
        } else if (arg == "--both") {
            use_classic = true;
            use_ml = true;
        } else if (arg == "--noar") {
            use_ar = false;
        } else if (arg == "--cross-val") {
            perform_cv = true;
        }
    }
    
    string method = use_median ? "median" : "average";
    cout << "Using " << method << " values for calculations.\n\n";

    // Load player stats
    vector<PlayerStats> all_player1_stats = load_all_player_stats(player1_file);
    vector<PlayerStats> all_player2_stats = load_all_player_stats(player2_file);
    PlayerStats player1 = load_player_stats(player1_file, use_median);
    PlayerStats player2 = load_player_stats(player2_file, use_median);
    
    // Count valid results for both players
    int valid_results = 0;
    for (const auto& p : all_player1_stats) {
        if (p.result >= 0) valid_results++;
    }
    for (const auto& p : all_player2_stats) {
        if (p.result >= 0) valid_results++;
    }
    
    cout << "Found " << valid_results << " valid match results across both players." << endl;
    
    // Extract player names from filenames
    string player1_name = player1_file.substr(player1_file.find_last_of("/\\") + 1);
    player1_name = player1_name.substr(0, player1_name.find_last_of("."));
    
    string player2_name = player2_file.substr(player2_file.find_last_of("/\\") + 1);
    player2_name = player2_name.substr(0, player2_name.find_last_of("."));
    
    // Print player stats summary
    print_player_stats(player1, player1_name);
    print_player_stats(player2, player2_name);

    cout << fixed << setprecision(2);
    
    // Calculate Adjusted Ratio if enabled
    double global_ar_coefficient = 1.0;
    double player1_ar = 1.0;
    double player2_ar = 1.0;
    
    if (use_ar) {
        cout << "--- Adjusted Ratio (AR) Analysis ---\n";
        
        // Calculate individual player ARs
        player1_ar = calculate_AR(player1);
        player2_ar = calculate_AR(player2);
        
        // Calculate global AR coefficient using regression
        vector<PlayerStats> all_stats;
        all_stats.insert(all_stats.end(), all_player1_stats.begin(), all_player1_stats.end());
        all_stats.insert(all_stats.end(), all_player2_stats.begin(), all_player2_stats.end());
        global_ar_coefficient = calculate_optimal_AR_coefficient(all_stats);
        
        cout << "Global AR coefficient: " << global_ar_coefficient << endl;
        cout << player1_name << " AR: " << player1_ar << endl;
        cout << player2_name << " AR: " << player2_ar << endl;
        cout << endl;
    }
    
    // Classic formula prediction
    if (use_classic) {
        double WspA = calculate_Wsp(player1);
        double WspB = calculate_Wsp(player2);
        
        // Apply AR if enabled
        if (use_ar) {
            WspA *= player1_ar;
            WspB *= player2_ar;
        }
        
        double CSA = WspA - WspB;
        double winrateA = 1.0 / (1.0 + exp(-CSA));
        double winrateB = 1.0 - winrateA;

        cout << "--- Classic Formula Prediction " << (use_ar ? "with AR" : "without AR") << " ---\n";
        cout << player1_name << " Wsp: " << WspA << endl;
        cout << player2_name << " Wsp: " << WspB << endl;
        cout << "CSA (combined score advantage): " << CSA << endl;
        cout << player1_name << " win probability: " << (winrateA * 100) << "%" << endl;
        cout << player2_name << " win probability: " << (winrateB * 100) << "%" << endl;
        cout << endl;
    }
    
    // ML prediction
    if (use_ml) {
        cout << "--- Machine Learning Prediction ---\n";
        
        // Generate training data from real player stats with actual results
        vector<MatchData> training_data = generate_real_training_data(all_player1_stats, all_player2_stats);
        
        if (training_data.empty()) {
            cout << "Not enough valid match results to train the ML model. Skipping ML prediction." << endl;
        } else {
            // Train the model
            LinearModel model(6);
            model.train(training_data);
            
            // Evaluate on the same training data
            evaluate_model(model, training_data);
            
            // Get feature importance
            auto importance = model.get_feature_importance();
            cout << "\nFeature importance ranking:\n";
            for (const auto& feat : importance) {
                cout << feat.first << ": " << feat.second << endl;
            }
            
            // Cross validation if requested
            if (perform_cv) {
                perform_cross_validation(training_data);
            }
            
            // Predict for our specific players
            vector<double> match_features = generate_features(player1, player2);
            double player1_win_prob = model.predict(match_features);
            double player2_win_prob = 1.0 - player1_win_prob;
            
            cout << "\nPrediction for " << player1_name << " vs " << player2_name << ":\n";
            cout << player1_name << " win probability: " << (player1_win_prob * 100) << "%" << endl;
            cout << player2_name << " win probability: " << (player2_win_prob * 100) << "%" << endl;
        }
    }
    
    // Make a final combined prediction if using both methods
    if (use_classic && use_ml) {
        // Calculate classic formula prediction
        double WspA = calculate_Wsp(player1);
        double WspB = calculate_Wsp(player2);
        
        // Apply AR if enabled
        if (use_ar) {
            WspA *= player1_ar;
            WspB *= player2_ar;
        }
        
        double CSA = WspA - WspB;
        double classic_winrateA = 1.0 / (1.0 + exp(-CSA));
        
        // Calculate ML prediction
        vector<MatchData> training_data = generate_real_training_data(all_player1_stats, all_player2_stats);
        
        if (training_data.empty()) {
            cout << "\n--- Combined Prediction Not Available ---\n";
            cout << "Not enough valid match results to train the ML model." << endl;
        } else {
            LinearModel model(6);
            model.train(training_data);
            vector<double> match_features = generate_features(player1, player2);
            double ml_winrateA = model.predict(match_features);
            
            // Average the two predictions
            double combined_winrateA = (classic_winrateA + ml_winrateA) / 2.0;
            double combined_winrateB = 1.0 - combined_winrateA;
            
            cout << "\n--- Combined Prediction (Classic + ML) ---\n";
            cout << player1_name << " win probability: " << (combined_winrateA * 100) << "%" << endl;
            cout << player2_name << " win probability: " << (combined_winrateB * 100) << "%" << endl;
        }
    }
    
    return 0;
}
