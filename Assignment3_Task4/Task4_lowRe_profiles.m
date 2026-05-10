clear; clc; close all;

saveFolder = 'assignment_plots';
if ~exist(saveFolder,'dir')
    mkdir(saveFolder);
end

%% ===== Literature data entered manually =====

% ROAMX-0201
roamx.alpha = [-4 -2 0 2 4 6 8 10 12]';
roamx.CL    = [-0.2 0.0 0.2 0.45 0.7 0.95 1.15 1.28 1.30]';
roamx.CD    = [0.08 0.07 0.065 0.062 0.065 0.075 0.090 0.115 0.150]';
roamx.name  = 'ROAMX-0201';

% CLF5605
clf.alpha = [-4 -2 0 2 4 6 8 10 12]';
clf.CL    = [-0.15 0.02 0.22 0.42 0.62 0.82 0.98 1.05 1.02]';
clf.CD    = [0.09 0.08 0.072 0.068 0.070 0.080 0.098 0.125 0.170]';
clf.name  = 'CLF5605';

% Circular-arc plate
circ.alpha = [-4 -2 0 2 4 6 8 10 12]';
circ.CL    = [-0.10 0.05 0.25 0.48 0.72 0.96 1.12 1.20 1.18]';
circ.CD    = [0.07 0.065 0.060 0.058 0.060 0.070 0.085 0.105 0.140]';
circ.name  = '5% Circular-Arc Plate';

profiles = [roamx, clf, circ];

%% Compute Cl/Cd
for i = 1:length(profiles)
    profiles(i).LD = profiles(i).CL ./ profiles(i).CD;
end

%% Plot Cl vs alpha
figure;
hold on; grid on;
for i = 1:length(profiles)
    plot(profiles(i).alpha, profiles(i).CL, 'LineWidth', 2, ...
        'DisplayName', profiles(i).name);
end
xlabel('\alpha [deg]');
ylabel('C_l');
title('C_l vs angle of attack from literature data');
legend('Location','best');
exportgraphics(gcf, fullfile(saveFolder,'cl_vs_AoA_T4_literature.png'),'Resolution',300);

%% Plot Cl vs Cd
figure;
hold on; grid on;
for i = 1:length(profiles)
    plot(profiles(i).CD, profiles(i).CL, 'LineWidth', 2, ...
        'DisplayName', profiles(i).name);
end
xlabel('C_d');
ylabel('C_l');
title('C_l vs C_d from literature data');
legend('Location','best');
exportgraphics(gcf, fullfile(saveFolder,'cl_vs_Cd_T4_literature.png'),'Resolution',300);

%% Plot Cl/Cd vs alpha
figure;
hold on; grid on;
for i = 1:length(profiles)
    plot(profiles(i).alpha, profiles(i).LD, 'LineWidth', 2, ...
        'DisplayName', profiles(i).name);
end
xlabel('\alpha [deg]');
ylabel('C_l / C_d');
title('Lift-to-drag ratio from literature data');
legend('Location','best');
exportgraphics(gcf, fullfile(saveFolder,'clcd_vs_AoA_T4_literature.png'),'Resolution',300);

%% Print max Cl/Cd
fprintf('Comparison of literature-based profiles\n\n');
for i = 1:length(profiles)
    [LDmax, idx] = max(profiles(i).LD);
    fprintf('%s\n', profiles(i).name);
    fprintf('Max Cl/Cd = %.2f at alpha = %.2f deg\n', LDmax, profiles(i).alpha(idx));
    fprintf('Cl = %.3f, Cd = %.4f\n\n', profiles(i).CL(idx), profiles(i).CD(idx));
end