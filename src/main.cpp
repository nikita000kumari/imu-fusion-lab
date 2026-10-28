// Replays the cleaned CSVs from the Python step through the C++ filter.
// Build: g++ -O2 -std=c++17 src/main.cpp -o build/fusion
// Run:   build/fusion data/processed/still_clean.csv data/processed/motion_clean.csv 0.98 1 1
// Output (stdout): t,roll,pitch
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "complementary_filter.h"

struct Row { double t, dt, ax, ay, az, gx, gy, gz; };

static std::vector<Row> readCsv(const std::string& path) {
    std::ifstream in(path);
    if (!in) { std::cerr << "cannot open " << path << "\n"; std::exit(1); }
    std::vector<Row> rows;
    std::string line;
    std::getline(in, line);  // header: t,dt,ax,ay,az,gx,gy,gz
    while (std::getline(in, line)) {
        for (char& c : line) if (c == ',') c = ' ';
        std::istringstream ss(line);
        Row r;
        if (ss >> r.t >> r.dt >> r.ax >> r.ay >> r.az >> r.gx >> r.gy >> r.gz) rows.push_back(r);
    }
    return rows;
}

int main(int argc, char** argv) {
    if (argc < 6) {
        std::cerr << "usage: fusion still.csv motion.csv alpha rollSign pitchSign\n";
        return 1;
    }
    const float alpha = std::atof(argv[3]);
    const float rollSign = std::atof(argv[4]);
    const float pitchSign = std::atof(argv[5]);

    // 1) "Boot" calibration: average the still recording
    imu::GyroCalibrator cal;
    for (const Row& r : readCsv(argv[1])) cal.addSample(r.gx, r.gy, r.gz);
    std::cerr << "bias: " << cal.biasX() << " " << cal.biasY() << " " << cal.biasZ() << "\n";

    // 2) Run the filter over the motion recording
    imu::ComplementaryFilter filter(alpha, rollSign, pitchSign);
    std::printf("t,roll,pitch\n");
    for (const Row& r : readCsv(argv[2])) {
        filter.update(r.ax, r.ay, r.az, r.gx - cal.biasX(), r.gy - cal.biasY(), r.dt);
        std::printf("%.6f,%.6f,%.6f\n", r.t, filter.roll(), filter.pitch());
    }
    return 0;
}
