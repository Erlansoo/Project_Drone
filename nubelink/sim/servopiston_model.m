%% servopiston_model.m — gemelo MATLAB del modelo Python (servopiston_model.py)
% Módulo Nubelink H1: 2 válvulas reductoras-relevadoras proporcionales (HYDAC PDR08-01,
% 0-20 bar) -> cámaras A/B -> pistón de doble vástago Ø32/Ø16 -> resorte de centrado del
% carrete + fricción + topes. Lazo de corriente con dither y lazo de posición PI opcional.
%
% Uso:  >> servopiston_model            (corre los 4 escenarios y dibuja las figuras)
% Sólo MATLAB base. Para el modelo físico "de verdad" usar Simscape Fluids (ver
% docs/simulacion_y_compras.md, sección "Blueprint Simscape").
%
% Unidades SI. Parámetros marcados SUPUESTO = medir en banco antes de confiar en ellos.

function servopiston_model()
    p = default_params();

    %% Escenario 1: escalones de corriente en lazo abierto (V_A)
    cmd = @(t) deal( 0.3*(t>=0.2 & t<0.9) + 0.6*(t>=0.9 & t<1.6) + 1.0*(t>=1.6 & t<2.3), 0 );
    r1 = simulate(p, 2.6, cmd, [], 1e-5, 100, inf);
    figure('Name','S1 escalones lazo abierto');
    subplot(3,1,1); plot(r1.t, r1.IA_cmd, '--', r1.t, r1.IA); ylabel('I_A [A]'); grid on; legend('consigna','bobina');
    subplot(3,1,2); plot(r1.t, r1.pA/1e5, r1.t, r1.pB/1e5); ylabel('p [bar]'); grid on; legend('A','B');
    subplot(3,1,3); plot(r1.t, r1.x*1e3); ylabel('x [mm]'); xlabel('t [s]'); grid on;
    fprintf('S1: x(0.3 A)=%.1f mm, x(0.6 A)=%.1f mm, x(1.0 A)=%.1f mm\n', ...
        1e3*r1.x(find(r1.t>=0.88,1)), 1e3*r1.x(find(r1.t>=1.58,1)), 1e3*r1.x(find(r1.t>=2.28,1)));

    %% Escenario 2: histéresis (rampa triangular lenta) con y sin dither
    for dith = [false true]
        p2 = p; p2.dither_on = dith;
        cmd2 = @(t) deal( p.I_max * min(t/3, (6-t)/3) .* (t<6), 0 );
        r2 = simulate(p2, 6.0, cmd2, [], 1e-5, 100, inf);
        figure('Name',sprintf('S2 histéresis dither=%d', dith));
        plot(r2.IA_cmd, r2.x*1e3); xlabel('I_A consigna [A]'); ylabel('x [mm]'); grid on;
        title(sprintf('Histéresis x(I), dither %s', string(dith)));
    end

    %% Escenario 3: falla segura — corte de corriente y de presión a carrera máxima
    cmd3 = @(t) deal( p.I_max*(t<1.0), 0 );
    r3 = simulate(p, 2.0, cmd3, [], 1e-5, 100, 1.0);
    figure('Name','S3 falla segura'); plot(r3.t, r3.x*1e3); grid on; xlabel('t [s]'); ylabel('x [mm]');
    i_ret = find(r3.t>1.0 & abs(r3.x)<1e-3, 1);
    fprintf('S3: retorno a |x|<1 mm en %.2f s tras el corte\n', r3.t(i_ret)-1.0);

    %% Escenario 3b: retorno ACTIVO a neutro en lazo cerrado y dump 0,5 s después (carrete sucio, 120 N)
    p3 = p; p3.Fc = 120;
    xref3 = @(t) 0.020*(t<1.0);
    r3c = simulate(p3, 2.0, [], xref3, 1e-5, 100, 1.5, 1.5);
    hold on; plot(r3c.t, r3c.x*1e3); legend('corte total','retorno activo + dump'); hold off;

    %% Escenario 4: lazo cerrado de posición (PI) con sensor
    xref = @(t) 1e-3*( 5*(t>=0.2 & t<1.2) + 15*(t>=1.2 & t<2.2) - 10*(t>=2.2 & t<3.2) );
    r4 = simulate(p, 3.4, [], xref, 1e-5, 100, inf);
    figure('Name','S4 lazo cerrado'); plot(r4.t, r4.x_ref*1e3, '--', r4.t, r4.x*1e3); grid on;
    xlabel('t [s]'); ylabel('x [mm]'); legend('consigna','posición');

    %% Modo manual
    mf = manual_mode_force(p, 0.1);
    fprintf('Modo manual (v=0.1 m/s): Q=%.1f L/min, dp=%.2f bar, F_hid=%.0f N + fricción %.0f N = %.0f N en la horquilla\n', ...
        mf.Q_lpm, mf.dp_bar, mf.F_hyd, mf.F_fric, mf.F_total);
end

function p = default_params()
    BAR = 1e5; LPM = 1/60000;
    p.A = pi/4*(0.032^2 - 0.016^2);   % m², camisa Ø32 / vástago Ø16
    p.x_max = 0.020;                  % carrera ±20 mm
    p.m = 0.8;                        % kg (SUPUESTO)
    p.F0 = 60;  p.c = 8000;           % N, N/m  resorte del carrete referido a la horquilla (SUPUESTO; medir)
    p.F0_mod = 50; p.c_mod = 2500;    % resorte de centrado propio del módulo (OBLIGATORIO): 50 N + 2,5 N/mm
    p.Fc = 45;  p.b = 300; p.v0 = 0.002;   % fricción (SUPUESTO; ensayo T2)
    p.k_stop = 5e6; p.d_stop = 5e3;
    p.p_s = 25*BAR;                   % pilotaje disponible
    p.V0 = 60e-6; p.beta = 8e8;       % volumen muerto + manguera; módulo efectivo (SUPUESTO)
    p.p_range = 20*BAR;               % PDR08-01 código 30
    p.I_max = 1.0; p.I0 = 0.12;       % A (SUPUESTO: confirmar bobina 24PG)
    p.tau_v = 0.015;                  % s
    p.Q_max = 12*LPM; p.G_v = (12*LPM)/(2*BAR);
    p.h_bl = 0.04;                    % A, histéresis mecánica de la válvula (SUPUESTO)
    p.tau_i = 0.003;                  % s, lazo de corriente
    p.dither_on = true; p.f_d = 150; p.I_d_frac = 0.05;
    p.Kp = 15; p.Ki = 250;            % A/m, A/(m·s)
end

function F = spring_force(x, F0, c)
    F = F0*tanh(x/2e-4) + c*x;
end

function F = friction_force(v, Fc, b, v0)
    F = Fc*tanh(v/v0) + b*v;
end

function Ie = backlash(I, Ie, h)
    if I > Ie + h/2,     Ie = I - h/2;
    elseif I < Ie - h/2, Ie = I + h/2;
    end
end

function r = simulate(p, T, cmd, xref, dt, decim, supply_cut_t, ctrl_off_t)
    if nargin < 8, ctrl_off_t = inf; end
    n = round(T/dt); nout = floor(n/decim)+1;
    r.t = zeros(nout,1); r.x = r.t; r.v = r.t; r.pA = r.t; r.pB = r.t;
    r.IA = r.t; r.IB = r.t; r.IA_cmd = r.t; r.IB_cmd = r.t; r.x_ref = r.t;
    A = p.A; m = p.m;
    x = 0; v = 0; pA = 0; pB = 0; IA = 0; IB = 0; IAe = 0; IBe = 0; pAr = 0; pBr = 0; integ = 0;
    K_v = p.p_range/(p.I_max - p.I0);
    if p.dither_on, I_d = p.I_d_frac*p.I_max; else, I_d = 0; end
    k = 1;
    for i = 0:n
        t = i*dt;
        xr = 0;
        if ~isempty(xref)
            xr = xref(t); e = xr - x; integ = integ + e*dt;
            u = p.Kp*e + p.Ki*integ; lim = p.I_max - p.I0;
            if abs(u) > lim, integ = integ - e*dt; u = max(-lim, min(lim, u)); end
            if u > 0, IAc = p.I0 + u; IBc = 0; else, IAc = 0; IBc = p.I0 - u; end
        else
            [IAc, IBc] = cmd(t);
        end
        if t >= ctrl_off_t, IAc = 0; IBc = 0; end
        dth = I_d*sin(2*pi*p.f_d*t);
        if IAc > 0, IAcd = max(0, IAc + dth); else, IAcd = 0; end
        if IBc > 0, IBcd = max(0, IBc + dth); else, IBcd = 0; end
        IA = IA + (IAcd - IA)/p.tau_i*dt;  IB = IB + (IBcd - IB)/p.tau_i*dt;
        IAe = backlash(IA, IAe, p.h_bl);   IBe = backlash(IB, IBe, p.h_bl);
        if t < supply_cut_t, ps = p.p_s; else, ps = 0; end
        pAs = min([max(K_v*(IAe - p.I0), 0), p.p_range, ps]);
        pBs = min([max(K_v*(IBe - p.I0), 0), p.p_range, ps]);
        pAr = pAr + (pAs - pAr)/p.tau_v*dt;  pBr = pBr + (pBs - pBr)/p.tau_v*dt;
        QA = max(-p.Q_max, min(p.Q_max, p.G_v*(pAr - pA)));
        QB = max(-p.Q_max, min(p.Q_max, p.G_v*(pBr - pB)));
        VA = p.V0 + A*x; VB = p.V0 - A*x;
        pA = max(pA + p.beta/VA*(QA - A*v)*dt, -0.5e5);
        pB = max(pB + p.beta/VB*(QB + A*v)*dt, -0.5e5);
        F = A*(pA - pB) - spring_force(x, p.F0, p.c) - spring_force(x, p.F0_mod, p.c_mod) - friction_force(v, p.Fc, p.b, p.v0);
        if x > p.x_max,      F = F - p.k_stop*(x - p.x_max) - p.d_stop*v;
        elseif x < -p.x_max, F = F - p.k_stop*(x + p.x_max) - p.d_stop*v; end
        v = v + F/m*dt; x = x + v*dt;
        if mod(i, decim) == 0
            r.t(k)=t; r.x(k)=x; r.v(k)=v; r.pA(k)=pA; r.pB(k)=pB; r.IA(k)=IA; r.IB(k)=IB;
            r.IA_cmd(k)=IAc; r.IB_cmd(k)=IBc; r.x_ref(k)=xr; k = k+1;
        end
    end
    f = fieldnames(r); for j = 1:numel(f), r.(f{j}) = r.(f{j})(1:k-1); end
end

function mf = manual_mode_force(p, v_manual)
    LPM = 1/60000;
    Q = p.A*v_manual; dp = Q/p.G_v; F_hyd = dp*p.A;
    mf = struct('v', v_manual, 'Q_lpm', Q/LPM, 'dp_bar', dp/1e5, 'F_hyd', F_hyd, 'F_fric', p.Fc, 'F_total', F_hyd + p.Fc);
end
