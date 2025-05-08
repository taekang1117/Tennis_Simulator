#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <random>
#include <chrono>
using namespace std;

struct PlayerStats {
    double DR;
    double A_percent;
    double DF_percent;
    double FirstIn;
    double FirstPercent;
    double SecondPercent;
};

struct MatchData {
    vector<double> features;  // Combined features of both players
    double result;            // 1 if player A won, 0 if player B won
};

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
        
        all_stats.push_back(stats);
    }

    return all_stats;
}

// Function to parse a CSV file and load aggregated player stats
PlayerStats load_player_stats(const string& filename, bool use_median = true) {
    vector<PlayerStats> all_stats = load_all_player_stats(filename);
    
    // Vectors to store all values
    vector<double> DR_values;
    vector<double> A_percent_values;
    vector<double> DF_percent_values;
    vector<double> FirstIn_values;
    vector<double> FirstPercent_values;
    vector<double> SecondPercent_values;
    
    // Extract values into separate vectors
    for (const auto& stats : all_stats) {
        DR_values.push_back(stats.DR);
        A_percent_values.push_back(stats.A_percent);
        DF_percent_values.push_back(stats.DF_percent);
        FirstIn_values.push_back(stats.FirstIn);
        FirstPercent_values.push_back(stats.FirstPercent);
        SecondPercent_values.push_back(stats.SecondPercent);
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
    } else {
        stats.DR = calculate_average(DR_values);
        stats.A_percent = calculate_average(A_percent_values);
        stats.DF_percent = calculate_average(DF_percent_values);
        stats.FirstIn = calculate_average(FirstIn_values);
        stats.FirstPercent = calculate_average(FirstPercent_values);
        stats.SecondPercent = calculate_average(SecondPercent_values);
    }

    return stats;
}

// Function to calculate Wsp score
double calculate_Wsp(const PlayerStats& p) {
    double A = p.A_percent / 100.0;
    double DF = p.DF_percent / 100.0;
    double FirstIn = p.FirstIn / 100.0;
    double FirstPercent = p.FirstPercent / 100.0;
    double SecondPercent = p.SecondPercent / 100.0;

    double Wa = A;
    double Wdf = DF * (-3);
    double W1st = (FirstIn - A) * FirstPercent * 2;
    double W2nd = (1 - FirstIn - DF) * SecondPercent * 4;
    double Wsp = (Wa) + (Wdf) + (W1st) + (W2nd);

    return Wsp;
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

// Generate synthetic training data based on historical patterns
vector<MatchData> generate_training_data(int num_samples = 1000) {
    vector<MatchData> training_data;
    unsigned seed = chrono::system_clock::now().time_since_epoch().count();
    default_random_engine generator(seed);
    
    // Generate balanced dataset
    for (int i = 0; i < num_samples; i++) {
        PlayerStats playerA, playerB;
        MatchData match;
        
        // Random DR values (typically between 0.5 and 3.0)
        normal_distribution<double> dr_dist(1.5, 0.5);
        playerA.DR = max(0.5, dr_dist(generator));
        playerB.DR = max(0.5, dr_dist(generator));
        
        // Random Ace percentages (typically between 0% and 20%)
        normal_distribution<double> ace_dist(10.0, 4.0);
        playerA.A_percent = max(0.0, min(25.0, ace_dist(generator)));
        playerB.A_percent = max(0.0, min(25.0, ace_dist(generator)));
        
        // Random Double Fault percentages (typically between 0% and 10%)
        normal_distribution<double> df_dist(4.0, 2.0);
        playerA.DF_percent = max(0.0, min(15.0, df_dist(generator)));
        playerB.DF_percent = max(0.0, min(15.0, df_dist(generator)));
        
        // Random First Serve In percentages (typically between 50% and 75%)
        normal_distribution<double> first_in_dist(65.0, 7.0);
        playerA.FirstIn = max(45.0, min(85.0, first_in_dist(generator)));
        playerB.FirstIn = max(45.0, min(85.0, first_in_dist(generator)));
        
        // Random First Serve Win percentages (typically between 60% and 85%)
        normal_distribution<double> first_win_dist(75.0, 7.0);
        playerA.FirstPercent = max(55.0, min(95.0, first_win_dist(generator)));
        playerB.FirstPercent = max(55.0, min(95.0, first_win_dist(generator)));
        
        // Random Second Serve Win percentages (typically between 40% and 65%)
        normal_distribution<double> second_win_dist(55.0, 7.0);
        playerA.SecondPercent = max(35.0, min(75.0, second_win_dist(generator)));
        playerB.SecondPercent = max(35.0, min(75.0, second_win_dist(generator)));
        
        // Calculate Wsp scores
        double WspA = calculate_Wsp(playerA);
        double WspB = calculate_Wsp(playerB);
        double CSA = WspA - WspB;
        
        // Determine match result based on sigmoid of CSA
        double win_prob = 1.0 / (1.0 + exp(-CSA));
        uniform_real_distribution<double> result_dist(0.0, 1.0);
        double random_outcome = result_dist(generator);
        
        // Generate features (differences between players)
        match.features = generate_features(playerA, playerB);
        
        // Set result (1 if player A wins, 0 if player B wins)
        match.result = (random_outcome < win_prob) ? 1.0 : 0.0;
        
        training_data.push_back(match);
    }
    
    return training_data;
}

void print_player_stats(const PlayerStats& stats, const string& player_name) {
    cout << "--- " << player_name << " Stats Summary ---\n";
    cout << "DR: " << stats.DR << endl;
    cout << "Ace %: " << stats.A_percent << "%" << endl;
    cout << "Double Fault %: " << stats.DF_percent << "%" << endl;
    cout << "First Serve In %: " << stats.FirstIn << "%" << endl;
    cout << "First Serve Win %: " << stats.FirstPercent << "%" << endl;
    cout << "Second Serve Win %: " << stats.SecondPercent << "%" << endl;
    cout << endl;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <Player1 CSV file> <Player2 CSV file> [options]\n";
        cerr << "Options:\n";
        cerr << "  --avg       Use average instead of median (default is median)\n";
        cerr << "  --classic   Use classic formula only\n";
        cerr << "  --ml        Use machine learning model only\n";
        cerr << "  --both      Use both classic and ML models (default)\n";
        return 1;
    }

    string player1_file = argv[1];
    string player2_file = argv[2];
    
    // Default options
    bool use_median = true;
    bool use_classic = true;
    bool use_ml = true;
    
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
        }
    }
    
    string method = use_median ? "median" : "average";
    cout << "Using " << method << " values for calculations.\n\n";

    PlayerStats player1 = load_player_stats(player1_file, use_median);
    PlayerStats player2 = load_player_stats(player2_file, use_median);
    
    // Extract player names from filenames
    string player1_name = player1_file.substr(player1_file.find_last_of("/\\") + 1);
    player1_name = player1_name.substr(0, player1_name.find_last_of("."));
    
    string player2_name = player2_file.substr(player2_file.find_last_of("/\\") + 1);
    player2_name = player2_name.substr(0, player2_name.find_last_of("."));
    
    // Print player stats summary
    print_player_stats(player1, player1_name);
    print_player_stats(player2, player2_name);

    cout << fixed << setprecision(2);
    
    // Classic formula prediction
    if (use_classic) {
        double WspA = calculate_Wsp(player1);
        double WspB = calculate_Wsp(player2);
        double CSA = WspA - WspB;
        double winrateA = 1.0 / (1.0 + exp(-CSA));
        double winrateB = 1.0 - winrateA;

        cout << "--- Classic Formula Prediction ---\n";
        cout << "WspA (" << player1_name << "): " << WspA << endl;
        cout << "WspB (" << player2_name << "): " << WspB << endl;
        cout << "CSA: " << CSA << endl;
        cout << player1_name << " Win Rate: " << winrateA * 100 << "%" << endl;
        cout << player2_name << " Win Rate: " << winrateB * 100 << "%" << endl;
        cout << endl;
    }
    
    // Machine learning prediction
    if (use_ml) {
        cout << "--- Machine Learning Prediction ---\n";
        
        // Generate synthetic training data
        vector<MatchData> training_data = generate_training_data(5000);
        
        // Train linear model
        LinearModel model(6, 0.1, 1000); // 6 features, learning rate 0.1, 1000 iterations
        model.train(training_data);
        
        // Generate features for our match
        vector<double> match_features = generate_features(player1, player2);
        
        // Make prediction
        double ml_winrateA = model.predict(match_features);
        double ml_winrateB = 1.0 - ml_winrateA;
        
        cout << player1_name << " Win Rate: " << ml_winrateA * 100 << "%" << endl;
        cout << player2_name << " Win Rate: " << ml_winrateB * 100 << "%" << endl;
        
        // Print feature importance
        cout << "\n--- Feature Importance ---\n";
        auto importance = model.get_feature_importance();
        for (const auto& feature : importance) {
            cout << feature.first << ": " << feature.second << endl;
        }
        cout << endl;
    }

    return 0;
}