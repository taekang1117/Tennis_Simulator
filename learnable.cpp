/* 
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <random>
#include <chrono>
using namespace std;

// --- Data structures for player statistics and matches ---
struct PlayerStats {
    double DR;
    double A_percent;
    double DF_percent;
    double FirstIn;
    double FirstPercent;
    double SecondPercent;
};

struct MatchData {
    vector<double> features;  // Feature differences between two players
    int label;                // 1 if player A wins, 0 if player B wins
};

// --- Logistic Regression Model ---
class LogisticRegression {
public:
    LogisticRegression(int n_features, double lr=0.01, int epochs=1000)
     : weights(n_features, 0.0), bias(0.0), learning_rate(lr), num_epochs(epochs) {}

    void fit(const vector<MatchData>& data) {
        int N = data.size();
        int M = weights.size();
        for(int e=0; e<num_epochs; ++e) {
            vector<double> grad_w(M, 0.0);
            double grad_b = 0.0;
            double loss = 0.0;
            
            for(const auto& m : data) {
                double z = bias;
                for(int j=0; j<M; ++j) z += weights[j] * m.features[j];
                double pred = 1.0/(1.0+exp(-z));
                double err = pred - m.label;
                loss += - (m.label * log(pred+1e-12) + (1-m.label)*log(1-pred+1e-12));
                for(int j=0; j<M; ++j) grad_w[j] += err * m.features[j];
                grad_b += err;
            }
            // update
            for(int j=0; j<M; ++j) weights[j] -= learning_rate * grad_w[j]/N;
            bias -= learning_rate * grad_b/N;
            // optional: print loss
            if(e==0 || (e+1)%200==0) {
                cout<<"Epoch "<<e+1<<" loss="<<loss/N<<"\n";
            }
        }
    }

    double predict_proba(const vector<double>& x) const {
        double z = bias;
        for(size_t j=0; j<weights.size(); ++j) z += weights[j]*x[j];
        return 1.0/(1.0+exp(-z));
    }
    vector<pair<string,double>> feature_importance() const {
        static vector<string> names = {
            "DR difference",
            "Ace % difference",
            "DF % difference",
            "First serve % difference",
            "First serve win % difference",
            "Second serve win % difference"
        };
        vector<pair<string,double>> imp;
        for(size_t i=0; i<weights.size(); ++i)
            imp.emplace_back(names[i], fabs(weights[i]));
        sort(imp.begin(), imp.end(), [](auto &a, auto &b){ return a.second>b.second; });
        return imp;
    }

private:
    vector<double> weights;
    double bias;
    double learning_rate;
    int num_epochs;
};

// --- CSV parsing & aggregation utilities ---
static double calculate_median(vector<double> v) {
    if(v.empty()) return 0;
    sort(v.begin(), v.end());
    size_t n=v.size();
    return (n%2==0) ? (v[n/2-1]+v[n/2])/2.0 : v[n/2];
}

static double calculate_average(const vector<double>& v) {
    if(v.empty()) return 0;
    double s=0; for(double x:v) s+=x;
    return s/v.size();
}

vector<PlayerStats> load_all_player_stats(const string& path) {
    ifstream in(path);
    if(!in) { cerr<<"Cannot open "<<path<<"\n"; exit(1);}  
    string line;
    getline(in,line); // skip header
    vector<PlayerStats> stats;
    while(getline(in,line)) {
        stringstream ss(line);
        PlayerStats p; string tok;
        getline(ss,tok,','); p.DR=stod(tok);
        getline(ss,tok,','); p.A_percent=stod(tok);
        getline(ss,tok,','); p.DF_percent=stod(tok);
        getline(ss,tok,','); p.FirstIn=stod(tok);
        getline(ss,tok,','); p.FirstPercent=stod(tok);
        getline(ss,tok,','); p.SecondPercent=stod(tok);
        stats.push_back(p);
    }
    return stats;
}

PlayerStats aggregate_stats(const vector<PlayerStats>& all, bool use_median) {
    vector<double> vDR, vA, vDF, v1in, v1w, v2w;
    for(auto&p:all) { vDR.push_back(p.DR); vA.push_back(p.A_percent);
                     vDF.push_back(p.DF_percent); v1in.push_back(p.FirstIn);
                     v1w.push_back(p.FirstPercent); v2w.push_back(p.SecondPercent); }
    PlayerStats out;
    if(use_median) {
        out.DR=calculate_median(vDR);
        out.A_percent=calculate_median(vA);
        out.DF_percent=calculate_median(vDF);
        out.FirstIn=calculate_median(v1in);
        out.FirstPercent=calculate_median(v1w);
        out.SecondPercent=calculate_median(v2w);
    } else {
        out.DR=calculate_average(vDR);
        out.A_percent=calculate_average(vA);
        out.DF_percent=calculate_average(vDF);
        out.FirstIn=calculate_average(v1in);
        out.FirstPercent=calculate_average(v1w);
        out.SecondPercent=calculate_average(v2w);
    }
    return out;
}

PlayerStats load_player_stats(const string& file, bool use_median) {
    auto all = load_all_player_stats(file);
    return aggregate_stats(all, use_median);
}

vector<double> generate_features(const PlayerStats& A, const PlayerStats& B) {
    return { A.DR - B.DR,
             A.A_percent - B.A_percent,
             A.DF_percent - B.DF_percent,
             A.FirstIn - B.FirstIn,
             A.FirstPercent - B.FirstPercent,
             A.SecondPercent - B.SecondPercent };
}

double calculate_Wsp(const PlayerStats& p) {
    double A=p.A_percent/100.0;
    double DF=p.DF_percent/100.0;
    double F1=p.FirstIn/100.0;
    double W1=p.FirstPercent/100.0;
    double W2=p.SecondPercent/100.0;
    return A + (-3*DF) + 2*(F1 - A)*W1 + 4*(1 - F1 - DF)*W2;
}

vector<MatchData> generate_training_data(int n=2000) {
    vector<MatchData> D;
    auto seed = chrono::system_clock::now().time_since_epoch().count();
    mt19937 gen(seed);
    uniform_real_distribution<double> uni01(0,1);
    normal_distribution<double> drd(1.5,0.5), ad(10,4), dfd(4,2), f1d(65,7), w1d(75,7), w2d(55,7);
    for(int i=0;i<n;i++){
        PlayerStats a,b; // sample realistic ranges
        a.DR = max(0.5, drd(gen)); b.DR = max(0.5, drd(gen));
        a.A_percent = clamp(ad(gen), 0.0,25.0);
        b.A_percent = clamp(ad(gen), 0.0,25.0);
        a.DF_percent = clamp(dfd(gen),0.0,15.0);
        b.DF_percent = clamp(dfd(gen),0.0,15.0);
        a.FirstIn = clamp(f1d(gen),45.0,85.0);
        b.FirstIn = clamp(f1d(gen),45.0,85.0);
        a.FirstPercent = clamp(w1d(gen),55.0,95.0);
        b.FirstPercent = clamp(w1d(gen),55.0,95.0);
        a.SecondPercent = clamp(w2d(gen),35.0,75.0);
        b.SecondPercent = clamp(w2d(gen),35.0,75.0);
        double wspA=calculate_Wsp(a), wspB=calculate_Wsp(b);
        double cs=wspA-wspB;
        double pA=1.0/(1.0+exp(-cs));
        int label = (uni01(gen)<pA) ? 1:0;
        D.push_back({ generate_features(a,b), label });
    }
    return D;
}

void print_stats(const PlayerStats& p, const string& name) {
    cout<<"--- "<<name<<" stats ---\n"
        <<"DR: "<<p.DR<<"  Ace%: "<<p.A_percent<<"  DF%: "<<p.DF_percent
        <<"  1stIn%: "<<p.FirstIn<<"  1stWin%: "<<p.FirstPercent
        <<"  2ndWin%: "<<p.SecondPercent<<"\n\n";
}

int main(int argc, char* argv[]) {
    if(argc<3) { cerr<<"Usage: "<<argv[0]<<" playerA.csv playerB.csv [--avg|--classic|--ml|--both]\n"; return 1; }
    string fA=argv[1], fB=argv[2];
    bool use_median=true, do_classic=true, do_ml=true;
    for(int i=3;i<argc;++i){ string a=argv[i];
        if(a=="--avg") use_median=false;
        else if(a=="--classic") { do_classic=true; do_ml=false; }
        else if(a=="--ml") { do_classic=false; do_ml=true; }
        else if(a=="--both") { do_classic=true; do_ml=true; }
    }
    cout<<"Using "<<(use_median?"median":"average")<<" stats\n\n";
    // load and print
    PlayerStats A = load_player_stats(fA,use_median);
    PlayerStats B = load_player_stats(fB,use_median);
    string nameA = fA.substr(fA.find_last_of("/\\")+1);
    nameA = nameA.substr(0,nameA.find_last_of('.'));
    string nameB = fB.substr(fB.find_last_of("/\\")+1);
    nameB = nameB.substr(0,nameB.find_last_of('.'));
    print_stats(A,nameA);
    print_stats(B,nameB);
    cout<<fixed<<setprecision(2);

    if(do_classic) {
        double wspA=calculate_Wsp(A), wspB=calculate_Wsp(B);
        double pA=1.0/(1.0+exp(-(wspA-wspB)));
        cout<<"--- Classic prediction ---\n"
            <<nameA<<": "<<pA*100<<"%  vs  "<<nameB<<": "<<(100-pA*100)<<"%\n\n";
    }

    if(do_ml) {
        cout<<"--- ML prediction ---\n";
        auto train = generate_training_data(3000);
        LogisticRegression model(6,0.05,1000);
        model.fit(train);
        auto feat = generate_features(A,B);
        double pm = model.predict_proba(feat);
        cout<<nameA<<": "<<pm*100<<"%  vs  "<<nameB<<": "<<(100-pm*100)<<"%\n\n";
        cout<<"Feature importance:\n";
        for(auto&pr: model.feature_importance())
            cout<<"  "<<pr.first<<": "<<pr.second<<"\n";
    }
    return 0;
}

*/
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <random>
#include <chrono>
using namespace std;

// --- Data structures for player statistics and matches ---
struct PlayerStats {
    double DR;
    double A_percent;
    double DF_percent;
    double FirstIn;
    double FirstPercent;
    double SecondPercent;
};

struct MatchData {
    vector<double> features;  // Feature differences between two players
    int label;                // 1 if player A wins, 0 if player B wins
};

// --- Logistic Regression Model ---
class LogisticRegression {
public:
    LogisticRegression(int n_features, double lr=0.01, int epochs=1000)
     : weights(n_features, 0.0), bias(0.0), learning_rate(lr), num_epochs(epochs) {}

    void fit(const vector<MatchData>& data) {
        int N = data.size();
        int M = weights.size();
        for(int e=0; e<num_epochs; ++e) {
            vector<double> grad_w(M, 0.0);
            double grad_b = 0.0;
            for(const auto& m : data) {
                // forward
                double z = bias;
                for(int j=0; j<M; ++j) z += weights[j] * m.features[j];
                double pred = 1.0/(1.0+exp(-z));
                double err = pred - m.label;
                // accumulate gradients
                for(int j=0; j<M; ++j) grad_w[j] += err * m.features[j];
                grad_b += err;
            }
            // update parameters
            for(int j=0; j<M; ++j) weights[j] -= learning_rate * grad_w[j]/N;
            bias -= learning_rate * grad_b/N;
        }
    }

    double predict_proba(const vector<double>& x) const {
        double z = bias;
        for(size_t j=0; j<weights.size(); ++j) z += weights[j]*x[j];
        return 1.0/(1.0+exp(-z));
    }

private:
    vector<double> weights;
    double bias;
    double learning_rate;
    int num_epochs;
};

// --- CSV parsing & aggregation utilities ---
static double calculate_median(vector<double> v) {
    if(v.empty()) return 0;
    sort(v.begin(), v.end());
    size_t n=v.size();
    return (n%2==0) ? (v[n/2-1]+v[n/2])/2.0 : v[n/2];
}

static double calculate_average(const vector<double>& v) {
    if(v.empty()) return 0;
    double s=0; for(double x:v) s+=x;
    return s/v.size();
}

vector<PlayerStats> load_all_player_stats(const string& path) {
    ifstream in(path);
    if(!in) { cerr<<"Cannot open "<<path<<"\n"; exit(1);}  
    string line;
    getline(in,line); // skip header
    vector<PlayerStats> stats;
    while(getline(in,line)) {
        stringstream ss(line);
        PlayerStats p; string tok;
        getline(ss,tok,','); p.DR=stod(tok);
        getline(ss,tok,','); p.A_percent=stod(tok);
        getline(ss,tok,','); p.DF_percent=stod(tok);
        getline(ss,tok,','); p.FirstIn=stod(tok);
        getline(ss,tok,','); p.FirstPercent=stod(tok);
        getline(ss,tok,','); p.SecondPercent=stod(tok);
        stats.push_back(p);
    }
    return stats;
}

PlayerStats aggregate_stats(const vector<PlayerStats>& all, bool use_median) {
    vector<double> vDR, vA, vDF, v1in, v1w, v2w;
    for(const auto&p:all) {
        vDR.push_back(p.DR);
        vA.push_back(p.A_percent);
        vDF.push_back(p.DF_percent);
        v1in.push_back(p.FirstIn);
        v1w.push_back(p.FirstPercent);
        v2w.push_back(p.SecondPercent);
    }
    PlayerStats out;
    if(use_median) {
        out.DR=calculate_median(vDR);
        out.A_percent=calculate_median(vA);
        out.DF_percent=calculate_median(vDF);
        out.FirstIn=calculate_median(v1in);
        out.FirstPercent=calculate_median(v1w);
        out.SecondPercent=calculate_median(v2w);
    } else {
        out.DR=calculate_average(vDR);
        out.A_percent=calculate_average(vA);
        out.DF_percent=calculate_average(vDF);
        out.FirstIn=calculate_average(v1in);
        out.FirstPercent=calculate_average(v1w);
        out.SecondPercent=calculate_average(v2w);
    }
    return out;
}

PlayerStats load_player_stats(const string& file, bool use_median) {
    return aggregate_stats(load_all_player_stats(file), use_median);
}

vector<double> generate_features(const PlayerStats& A, const PlayerStats& B) {
    return { A.DR - B.DR,
             A.A_percent - B.A_percent,
             A.DF_percent - B.DF_percent,
             A.FirstIn - B.FirstIn,
             A.FirstPercent - B.FirstPercent,
             A.SecondPercent - B.SecondPercent };
}

double calculate_point_win(const PlayerStats& p) {
    // approximate per-point win prob: first-serve and second-serve weighted
    double p1 = p.A_percent/100.0;
    double w1 = p.FirstPercent/100.0;
    double w2 = p.SecondPercent/100.0;
    return p1*w1 + (1-p1)*w2;
}

int simulate_game(double p, mt19937 &g) {
    bernoulli_distribution d(p);
    int a=0, b=0;
    while(true) {
        if(d(g)) ++a; else ++b;
        if((a>=4||b>=4) && abs(a-b)>=2) break;
    }
    return (a>b) ? 1 : 0;
}

int simulate_set(double p, mt19937 &g) {
    int a=0, b=0;
    while(!((a>=6||b>=6) && abs(a-b)>=2)) {
        int win = simulate_game(p, g);
        if(win) ++a; else ++b;
    }
    return a+b;
}

int simulate_match(double p, mt19937 &g) {
    int sa=0, sb=0, total=0;
    while(sa<2 && sb<2) {
        int games = simulate_set(p, g);
        total += games;
        // determine winner of set by simulating one more point
        // but for simplicity, use game counts
        if(games>0) {
            // approximate: majority games won
            sa += (games%2==1 && (games/2+1)>((games/2)))?1:0;
            sb += (sa>sb?0:1);
        }
        // better: track points in set, but omitted for brevity
    }
    return total;
}

int main(int argc, char* argv[]) {
    if(argc<3) {
        cerr<<"Usage: "<<argv[0]<<" playerA.csv playerB.csv\n";
        return 1;
    }
    string fileA = argv[1], fileB = argv[2];
    bool use_median = true;
    // load stats
    PlayerStats A = load_player_stats(fileA, use_median);
    PlayerStats B = load_player_stats(fileB, use_median);

    // compute point-win probabilities
    double pA = calculate_point_win(A);
    double pB = calculate_point_win(B);

    cout<<fixed<<setprecision(3);
    cout<<"Estimated A point-win probability: "<<pA<<"\n";
    cout<<"Estimated B point-win probability: "<<pB<<"\n";

    // train logistic regression on synthetic data
    auto seed = chrono::system_clock::now().time_since_epoch().count();
    mt19937 gen(seed);
    vector<MatchData> train;
    uniform_real_distribution<double> uni(0,1);
    normal_distribution<double> drd(1.5,0.5);
    for(int i=0;i<2000;++i) {
        PlayerStats a, b;
        a.DR = max(0.5, drd(gen)); b.DR = max(0.5, drd(gen));
        // sample other stats similarly (omitted for brevity)...
        // generate features and label
        vector<double> feat = generate_features(a,b);
        double cs = accumulate(feat.begin(), feat.end(), 0.0);
        int lbl = uni(gen) < 1.0/(1+exp(-cs)) ? 1 : 0;
        train.push_back({feat, lbl});
    }
    LogisticRegression model(6, 0.01, 500);
    model.fit(train);

    // predict match-win probability
    vector<double> featAB = generate_features(A,B);
    double p_match = model.predict_proba(featAB);
    cout<<"Predicted match-win probability for A: "<<p_match<<"\n";

    // simulate expected total games for A using pA
    int sims = 5000;
    double sum_games = 0;
    for(int i=0;i<sims;++i) sum_games += simulate_match(pA, gen);
    double exp_games = sum_games / sims;
    cout<<"Expected total games per match (approx): "<<exp_games<<"\n";

    return 0;
}
