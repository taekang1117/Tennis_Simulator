import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import * as Papa from 'papaparse';

export default function TennisAnalysis() {
  const [player1Data, setPlayer1Data] = useState([]);
  const [player2Data, setPlayer2Data] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [activeTab, setActiveTab] = useState('stats'); // 'stats', 'prediction', or 'ar'
  
  // Array of colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  useEffect(() => {
    // Load the CSV files
    const loadCSVs = async () => {
      try {
        const sinnerFile = await window.fs.readFile('sinner.csv', { encoding: 'utf8' });
        const benFile = await window.fs.readFile('ben.csv', { encoding: 'utf8' });
        
        // Parse CSVs
        const sinnerData = Papa.parse(sinnerFile, { 
          header: true, 
          dynamicTyping: true, 
          skipEmptyLines: true 
        }).data;
        
        const benData = Papa.parse(benFile, { 
          header: true, 
          dynamicTyping: true, 
          skipEmptyLines: true 
        }).data;
        
        // Transform data for analysis
        const transformedSinnerData = sinnerData.map(row => ({
          DR: row.DR,
          A: row['A%'],
          DF: row['DF%'],
          FirstIn: row['1stIn'],
          FirstPercent: row['1st%'],
          SecondPercent: row['2nd%'],
          TW: row['TW%']
        }));
        
        const transformedBenData = benData.map(row => ({
          DR: row.DR,
          A: row['A%'],
          DF: row['DF%'],
          FirstIn: row['1stIn'],
          FirstPercent: row['1st%'],
          SecondPercent: row['2nd%'],
          TW: row['TW%']
        }));
        
        // Set state
        setPlayer1Data(transformedSinnerData);
        setPlayer2Data(transformedBenData);
        
        // Generate comparison data
        const compData = generateComparison(transformedSinnerData, transformedBenData);
        setComparison(compData);
        
        // Generate predictions
        const preds = generatePredictions(transformedSinnerData, transformedBenData);
        setPredictions(preds);
      } catch (error) {
        console.error('Error loading CSV files:', error);
      }
    };
    
    loadCSVs();
  }, []);
  
  // Function to calculate Wsp score
  const calculateWsp = (player) => {
    const A = player.A / 100.0;
    const DF = player.DF / 100.0;
    const FirstIn = player.FirstIn / 100.0;
    const FirstPercent = player.FirstPercent / 100.0;
    const SecondPercent = player.SecondPercent / 100.0;

    const Wa = A;
    const Wdf = DF * (-3);
    const W1st = (FirstIn - A) * FirstPercent * 4;
    const W2nd = (1 - FirstIn - DF) * SecondPercent * 2.5;
    const Wsp = (Wa) + (Wdf) + (W1st) + (W2nd);

    return Wsp;
  };
  
  // Function to calculate AR (Adjusted Ratio)
  const calculateAR = (player) => {
    const Wsp = calculateWsp(player);
    const TW = player.TW / 100.0;
    
    // Convert Wsp to win probability
    const WspProb = 1.0 / (1.0 + Math.exp(-Wsp));
    
    // Avoid division by very small numbers
    if (Math.abs(WspProb) < 0.01) {
      return TW / 0.01;
    }
    
    return TW / WspProb;
  };
  
  // Function to calculate optimal AR coefficient
  const calculateOptimalAR = (players) => {
    // Prepare data for linear regression
    const X = []; // Original win probabilities
    const Y = []; // True win percentages
    
    players.forEach(player => {
      const Wsp = calculateWsp(player);
      const winProb = 1.0 / (1.0 + Math.exp(-Wsp));
      X.push(winProb);
      Y.push(player.TW / 100.0);
    });
    
    // Simple linear regression (Y = k*X)
    let sumXY = 0;
    let sumX2 = 0;
    
    for (let i = 0; i < X.length; i++) {
      sumXY += X[i] * Y[i];
      sumX2 += X[i] * X[i];
    }
    
    // Avoid division by zero
    if (sumX2 < 0.0001) {
      return 1.0;
    }
    
    return sumXY / sumX2;
  };
  
  // Function to generate comparison data
  const generateComparison = (player1Array, player2Array) => {
    // Calculate average stats for each player
    const getAverageStats = (playerArray) => {
      const sum = {};
      const keys = ['DR', 'A', 'DF', 'FirstIn', 'FirstPercent', 'SecondPercent', 'TW'];
      
      // Initialize sums
      keys.forEach(key => {
        sum[key] = 0;
      });
      
      // Sum all values
      playerArray.forEach(player => {
        keys.forEach(key => {
          sum[key] += player[key];
        });
      });
      
      // Calculate averages
      const avg = {};
      keys.forEach(key => {
        avg[key] = sum[key] / playerArray.length;
      });
      
      return avg;
    };
    
    const player1Avg = getAverageStats(player1Array);
    const player2Avg = getAverageStats(player2Array);
    
    // Calculate Wsp scores
    const player1Wsp = calculateWsp(player1Avg);
    const player2Wsp = calculateWsp(player2Avg);
    
    // Calculate AR values
    const player1AR = calculateAR(player1Avg);
    const player2AR = calculateAR(player2Avg);
    
    // Calculate adjusted Wsp scores
    const player1AdjWsp = player1Wsp * player1AR;
    const player2AdjWsp = player2Wsp * player2AR;
    
    // Build comparison data
    const comparisonData = [
      {
        category: 'DR',
        'Sinner': player1Avg.DR,
        'Ben': player2Avg.DR,
        'Difference': player1Avg.DR - player2Avg.DR
      },
      {
        category: 'Ace %',
        'Sinner': player1Avg.A,
        'Ben': player2Avg.A,
        'Difference': player1Avg.A - player2Avg.A
      },
      {
        category: 'Double Fault %',
        'Sinner': player1Avg.DF,
        'Ben': player2Avg.DF,
        'Difference': player1Avg.DF - player2Avg.DF
      },
      {
        category: 'First Serve %',
        'Sinner': player1Avg.FirstIn,
        'Ben': player2Avg.FirstIn,
        'Difference': player1Avg.FirstIn - player2Avg.FirstIn
      },
      {
        category: 'First Serve Win %',
        'Sinner': player1Avg.FirstPercent,
        'Ben': player2Avg.FirstPercent,
        'Difference': player1Avg.FirstPercent - player2Avg.FirstPercent
      },
      {
        category: 'Second Serve Win %',
        'Sinner': player1Avg.SecondPercent,
        'Ben': player2Avg.SecondPercent,
        'Difference': player1Avg.SecondPercent - player2Avg.SecondPercent
      },
      {
        category: 'True Win %',
        'Sinner': player1Avg.TW,
        'Ben': player2Avg.TW,
        'Difference': player1Avg.TW - player2Avg.TW
      }
    ];
    
    return comparisonData;
  };
  
  // Function to generate predictions
  const generatePredictions = (player1Array, player2Array) => {
    // Calculate average stats for each player
    const getAverageStats = (playerArray) => {
      const sum = {};
      const keys = ['DR', 'A', 'DF', 'FirstIn', 'FirstPercent', 'SecondPercent', 'TW'];
      
      // Initialize sums
      keys.forEach(key => {
        sum[key] = 0;
      });
      
      // Sum all values
      playerArray.forEach(player => {
        keys.forEach(key => {
          sum[key] += player[key];
        });
      });
      
      // Calculate averages
      const avg = {};
      keys.forEach(key => {
        avg[key] = sum[key] / playerArray.length;
      });
      
      return avg;
    };
    
    const player1Avg = getAverageStats(player1Array);
    const player2Avg = getAverageStats(player2Array);
    
    // Calculate Wsp scores
    const player1Wsp = calculateWsp(player1Avg);
    const player2Wsp = calculateWsp(player2Avg);
    
    // Calculate win probabilities (original)
    const CSA = player1Wsp - player2Wsp;
    const player1WinRate = 1.0 / (1.0 + Math.exp(-CSA));
    const player2WinRate = 1.0 - player1WinRate;
    
    // Calculate AR for both players
    const player1AR = calculateAR(player1Avg);
    const player2AR = calculateAR(player2Avg);
    
    // Calculate optimal global AR coefficient
    const allPlayers = [...player1Array, ...player2Array];
    const globalAR = calculateOptimalAR(allPlayers);
    
    // Calculate adjusted Wsp scores
    const player1AdjWsp = player1Wsp * player1AR;
    const player2AdjWsp = player2Wsp * player2AR;
    
    // Calculate adjusted win probabilities
    const adjCSA = player1AdjWsp - player2AdjWsp;
    const player1AdjWinRate = 1.0 / (1.0 + Math.exp(-adjCSA));
    const player2AdjWinRate = 1.0 - player1AdjWinRate;
    
    return {
      original: {
        player1Wsp,
        player2Wsp,
        player1WinRate,
        player2WinRate
      },
      adjusted: {
        player1AR,
        player2AR,
        globalAR,
        player1AdjWsp,
        player2AdjWsp,
        player1AdjWinRate,
        player2AdjWinRate
      }
    };
  };
  
  // Function to format percentage
  const formatPercent = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };
  
  // Generate prediction data for charts
  const generatePredictionChartData = () => {
    if (!predictions) return [];
    
    return [
      {
        name: 'Original',
        'Sinner': predictions.original.player1WinRate * 100,
        'Ben': predictions.original.player2WinRate * 100
      },
      {
        name: 'Adjusted with AR',
        'Sinner': predictions.adjusted.player1AdjWinRate * 100,
        'Ben': predictions.adjusted.player2AdjWinRate * 100
      }
    ];
  };
  
  // Generate AR comparison data for charts
  const generateARComparisonData = () => {
    if (!predictions) return [];
    
    return [
      {
        name: 'Original Wsp',
        'Sinner': predictions.original.player1Wsp,
        'Ben': predictions.original.player2Wsp
      },
      {
        name: 'Adjusted Wsp',
        'Sinner': predictions.adjusted.player1AdjWsp,
        'Ben': predictions.adjusted.player2AdjWsp
      }
    ];
  };
  
  // Generate pie chart data for win predictions
  const generateWinPredictionData = () => {
    if (!predictions) return [];
    
    return [
      { name: 'Sinner', value: predictions.adjusted.player1AdjWinRate * 100 },
      { name: 'Ben', value: predictions.adjusted.player2AdjWinRate * 100 }
    ];
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Tennis Prediction Analysis</h1>
      
      {/* Tab Navigation */}
      <div className="flex mb-6">
        <button 
          className={`px-4 py-2 ${activeTab === 'stats' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('stats')}
        >
          Player Stats
        </button>
        <button 
          className={`px-4 py-2 ${activeTab === 'prediction' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('prediction')}
        >
          Win Predictions
        </button>
        <button 
          className={`px-4 py-2 ${activeTab === 'ar' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('ar')}
        >
          Adjusted Ratio (AR)
        </button>
      </div>
      
      {/* Content based on active tab */}
      {activeTab === 'stats' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Player Statistics Comparison</h2>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={comparison}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Sinner" fill="#8884d8" />
                <Bar dataKey="Ben" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {activeTab === 'prediction' && predictions && (
        <div>
          <h2 className="text-xl font-bold mb-4">Win Probability Predictions</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Win Probabilities</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={generatePredictionChartData()}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis label={{ value: 'Win Probability (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Sinner" fill="#8884d8" />
                    <Bar dataKey="Ben" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Adjusted Win Probability</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={generateWinPredictionData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(2)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {generateWinPredictionData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">Prediction Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded">
                <h4 className="font-bold">Original Prediction</h4>
                <p>Sinner Win Rate: {formatPercent(predictions.original.player1WinRate)}</p>
                <p>Ben Win Rate: {formatPercent(predictions.original.player2WinRate)}</p>
                <p>Original Wsp (Sinner): {predictions.original.player1Wsp.toFixed(4)}</p>
                <p>Original Wsp (Ben): {predictions.original.player2Wsp.toFixed(4)}</p>
              </div>
              
              <div className="p-4 border rounded">
                <h4 className="font-bold">AR-Adjusted Prediction</h4>
                <p>Sinner Win Rate: {formatPercent(predictions.adjusted.player1AdjWinRate)}</p>
                <p>Ben Win Rate: {formatPercent(predictions.adjusted.player2AdjWinRate)}</p>
                <p>Adjusted Wsp (Sinner): {predictions.adjusted.player1AdjWsp.toFixed(4)}</p>
                <p>Adjusted Wsp (Ben): {predictions.adjusted.player2AdjWsp.toFixed(4)}</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {activeTab === 'ar' && predictions && (
        <div>
          <h2 className="text-xl font-bold mb-4">Adjusted Ratio (AR) Analysis</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Wsp Score Comparison</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={generateARComparisonData()}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Sinner" fill="#8884d8" />
                    <Bar dataKey="Ben" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="p-4 border rounded">
              <h3 className="text-lg font-semibold mb-2">Adjusted Ratio Details</h3>
              <p>Global AR Coefficient: {predictions.adjusted.globalAR.toFixed(4)}</p>
              <p>Sinner AR: {predictions.adjusted.player1AR.toFixed(4)}</p>
              <p>Ben AR: {predictions.adjusted.player2AR.toFixed(4)}</p>
              <div className="mt-4">
                <h4 className="font-bold">Formula Explanation:</h4>
                <p className="mt-2">
                  The Adjusted Ratio (AR) fine-tunes the prediction model by scaling the Wsp score to better match 
                  actual win rates (TW). The formula is:
                </p>
                <p className="mt-2 font-mono">AR = True Win % / Win probability from original Wsp</p>
                <p className="mt-2">
                  The new adjusted Wsp score is calculated as:
                </p>
                <p className="mt-2 font-mono">Adjusted Wsp = Original Wsp * AR</p>
                <p className="mt-2">
                  This helps calibrate predictions to match historical performance more accurately.
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">Impact of AR on Predictions</h3>
            <p>
              The AR adjustment helps align the theoretical win probabilities derived from player statistics with 
              their actual performance history. By incorporating the True Win percentage data, the model can better 
              account for intangible factors not captured by the basic statistics alone.
            </p>
            <p className="mt-2">
              Players with an AR > 1 tend to win more matches than their statistics would suggest, while players 
              with an AR < 1 win fewer matches than expected based on their statistics.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}