# inno-terminals-tanks

> 🛠️ **The software implementation of this SRS has been completed.** For architecture, setup and mapping
> of requirements to code: [`PROJECT.md`](PROJECT.md) · [`docs/SRS-TRACEABILITY.md`](docs/SRS-TRACEABILITY.md) ·
> Dedicated encrypted modules (Appendix 5.3): [`docs/IP-VAULT.md`](docs/IP-VAULT.md)
>
> Run: `docker compose up --build` — or the manual guide in `PROJECT.md`.

---

Software Requirements Specification (SRS)
IoT- and AI-Based Integrated Safety and Operations Management System for Petrochemical Terminals and Tanks
Version: 1.0
Date: 2025-04-08
Prepared by: System Analysis and Design Team

Table of Contents
Introduction
1.1 Purpose
1.2 Scope
1.3 Definitions, Acronyms and Terms
1.4 References
1.5 Document Overview

General Description
2.1 Product Vision
2.2 Product Functions
2.3 User Classes and Characteristics
2.4 Operating Environment
2.5 Design and Implementation Constraints
2.6 Assumptions and Dependencies

Specific Requirements
3.1 Functional Requirements
3.1.1 Real-Time Tank Monitoring Module
3.1.2 Leak Prediction Module
3.1.3 Loading/Unloading Operations Optimization Module
3.1.4 Alert and Event Management Module
3.1.5 Reporting and Analytics Module
3.1.6 Integration Module with Existing Systems
3.2 Non-Functional Requirements
3.2.1 Performance
3.2.2 Reliability
3.2.3 Security
3.2.4 Maintainability
3.2.5 Portability
3.2.6 Scalability
3.2.7 Standards Compliance

External Interface Requirements
4.1 User Interface
4.2 Hardware Interface
4.3 Software Interface
4.4 Communication Interface

Appendices
5.1 Synthetic Data Generation Code
5.2 International Benchmarks
5.3 Patentable Aspects

1. Introduction
1.1 Purpose
The purpose of this document is to specify the complete requirements for the design, development and deployment of an IoT- and AI-based integrated safety and operations management system for petrochemical terminals and tanks. Using Internet of Things (IoT) sensors and artificial intelligence (AI) algorithms, this system enables real-time monitoring of tank status, prediction of potential leaks, and optimization of loading and unloading operations.

1.2 Scope
This system is designed for use in storage and transfer terminals for petroleum, petrochemical and gas products. The scope includes:

Continuous monitoring of physical and chemical parameters of tanks (temperature, pressure, level, gas composition, vibration, corrosion, etc.)

Real-time data analysis for anomaly detection and leak prediction

Optimizing the scheduling and sequence of loading/unloading operations while considering safety and productivity

Providing early warnings and event management

Integration with Distributed Control Systems (DCS), Management Information Systems (MIS) and Enterprise Resource Planning (ERP) systems

1.3 Definitions, Acronyms and Terms
IoT: Internet of Things

AI/ML: Artificial Intelligence / Machine Learning

DCS: Distributed Control System

SCADA: Supervisory Control and Data Acquisition

API: Application Programming Interface

MES: Manufacturing Execution System

ERP: Enterprise Resource Planning

ATEX: Standard for electrical equipment in explosive atmospheres

IEC 61511: Standard for safety instrumented systems

API RP 2350: Recommended practice for protecting storage tanks against overfill

IEC 62443: Cybersecurity standard for industrial automation and control systems

DT: Digital Twin

Leak prediction: Estimating the probability of a leak occurring in the near future based on analysis of data patterns

1.4 References
ISO/IEC/IEEE 29148:2018 – Systems and software engineering — Requirements engineering

ISO 15926 – Industrial automation systems and integration

ISO 14224 – Petroleum, petrochemical and natural gas industries — Collection and exchange of reliability and maintenance data

IEC 61511 – Functional safety — Safety instrumented systems for the process industry sector

API RP 2350 – Overfill Protection for Storage Tanks in Petroleum Facilities

IEC 62443 – Industrial communication networks — Network and system security

ISA‑95 – Enterprise‑Control System Integration

NFPA 30 – Flammable and Combustible Liquids Code

1.5 Document Overview
This document is organized into the following sections: Section 2 General system description, Section 3 Functional and non-functional requirements, Section 4 External interface requirements, and Section 5 Appendices including synthetic data generation code, international benchmarks and patentable aspects.

2. General Description
2.1 Product Vision
This product operates as an integrated software-hardware platform which, by deploying a network of smart sensors on tanks and pipelines, collects data in real time and, using machine learning models, provides advanced analytics for leak prediction, equipment failure detection and operations optimization. The system must be deployable in large terminals with hundreds of tanks and also scalable for small terminals.

2.2 Product Functions
The main functions of the product are:

Real-time monitoring: Displaying the instantaneous status of critical parameters of each tank (level, temperature, pressure, density, composition of flammable and toxic gases, vibration, corrosion rate)

Leak prediction: Using ML models trained on historical and real-time data to identify patterns leading to a leak and generate a high-accuracy preventive alert

Loading/unloading optimization: Optimization algorithms for scheduling loading and unloading operations with the goal of reducing waiting time, preventing overflow, and respecting safety and capacity constraints

Alert management: An intelligent alert prioritization system, sending notifications to operators via mobile/email/SMS, and recording and tracking events

Reporting and analytics: Management dashboards, periodic reports, trend analysis, and the ability to search historical data

Integration: Connection to DCS/SCADA, maintenance systems (CMMS), and enterprise software through APIs and standard industrial protocols

2.3 User Classes and Characteristics
Control room operator: View the real-time dashboard, receive alerts, acknowledge events

Safety engineer: Analyze safety reports, configure thresholds, review leak predictions

Operations manager: View KPIs, optimal loading/unloading planning, strategic decision-making

Maintenance technician: View equipment health status, receive preventive work orders

Senior manager: Executive dashboard, cost-benefit analysis, compliance reports

2.4 Operating Environment
Hardware: Central servers (on-premise or cloud), industrial IoT gateways, wireless sensors (ATEX/IECEx compliant for hazardous areas), operator workstations

Software: Server operating system (Linux/Windows Server), time-series database (such as InfluxDB, TimescaleDB), stream processing engine (Apache Kafka, Flink), ML model runtime environment (TensorFlow Serving, ONNX Runtime)

Network: Isolated, highly secure industrial network, support for MQTT, OPC-UA, Modbus TCP protocols

2.5 Design and Implementation Constraints
All hardware installed in hazardous areas must have ATEX/IECEx certification.

The system must respond with minimal latency (less than 1 second for critical data).

AI models must be explainable (Explainable AI) so operators can understand the reasons for predictions.

The system must have temporary offline operation capability if the connection to the central server is lost (edge computing).

2.6 Assumptions and Dependencies
Sufficient historical data from similar tanks is available to train ML models or is created through the synthetic data generation code (Section 5.1).

Industrial network infrastructure with sufficient bandwidth for transmitting sensor data is provided.

Local and international safety and environmental standards are observed.

3. Specific Requirements
3.1 Functional Requirements
3.1.1 Real-Time Tank Monitoring Module
FR-1.1: The system must collect data from sensors installed on tanks (level, temperature, pressure, density, flammable gas, H2S, vibration, corrosion) at a sampling rate of at least 1 Hz.

FR-1.2: Data must be received from IoT gateways through MQTT/OPC-UA/Modbus protocols and stored in the time-series database.

FR-1.3: The real-time dashboard must display the status of each tank with a color code (green/yellow/red) based on configured thresholds.

FR-1.4: The system must provide time zoom capability and display of parameter trends over arbitrary intervals (1 minute to 1 year).

FR-1.5: The operator must be able to set alert thresholds (upper/lower limit, critical limit) for each parameter.

3.1.2 Leak Prediction Module
FR-2.1: The system must use machine learning models (such as LSTM, Isolation Forest, Autoencoder) to detect anomalies in real-time data.

FR-2.2: Leak prediction models must be trained on historical data (including synthetic data generated per Section 5.1) and retrained periodically (e.g., monthly).

FR-2.3: Leak prediction must be made with a horizon of at least 30 minutes before the possible occurrence, and the alert must provide the probability of occurrence (e.g., 85%) and a confidence interval.

FR-2.4: The system must have Explainability: showing the most important parameters that led to the leak prediction (using SHAP or LIME).

FR-2.5: If a real leak is detected (based on gas sensors or pressure drop), the system must immediately issue an automatic shutoff command for the relevant valves (if connected to the safety system) (with override capability by an authorized operator).

FR-2.6: The accuracy of the leak prediction model must be at least 95% (Recall ≥ 0.95) with a false alarm rate of less than 5%. To achieve this accuracy, the synthetic data generated in Section 5.1 should be used.

3.1.3 Loading/Unloading Operations Optimization Module
FR-3.1: The system must provide an optimal loading/unloading plan based on tank capacities, pump flow rates, safety constraints (maximum allowable level, pressure), and transport schedules.

FR-3.2: The optimization algorithm must minimize the total operation time and maximize capacity utilization using operations research methods (such as mixed-integer linear programming - MILP) or metaheuristic algorithms (Genetic Algorithm, Particle Swarm).

FR-3.3: The system must provide the ability to simulate different scenarios (What-If) to evaluate the impact of changes (e.g., a pump failure).

FR-3.4: The optimized plan must be integrated with ERP/MES systems through an API so that loading orders are received automatically and status is updated.

FR-3.5: During operations, the system must monitor flow rate, tank level and pressure in real time and issue a corrective alert if there is a deviation from the plan.

3.1.4 Alert and Event Management Module
FR-4.1: All alerts must be stored in a prioritized queue (by severity: critical, high, medium, low).

FR-4.2: Sending notifications to the relevant operators through multiple channels (mobile, email, SMS, industrial loudspeakers) with receipt acknowledgment capability.

FR-4.3: Critical alerts must require two-step confirmation (Two-person rule).

FR-4.4: The system must record a complete report of each event including time, related parameters, actions taken and the operator's digital signature.

FR-4.5: Intelligent suppression (Suppression) of repeated alerts caused by a single cause.

3.1.5 Reporting and Analytics Module
FR-5.1: Automatic generation of daily, weekly and monthly reports including safety KPIs (number of alerts, response time, correct/incorrect predictions).

FR-5.2: Management dashboard with interactive charts for analyzing parameter trends, comparing tank performance, and identifying bottlenecks.

FR-5.3: Advanced search capability in historical data by time interval, tank, event type, etc.

FR-5.4: Compliance reports with API RP 2350 and IEC 61511 standards including safety proof documentation.

3.1.6 Integration Module with Existing Systems
FR-6.1: Connection to DCS/SCADA through the OPC-UA protocol to receive process data and send control commands (with security restrictions).

FR-6.2: Connection to CMMS (maintenance management system) for automatic sending of preventive work orders based on equipment health status.

FR-6.3: Connection to ERP systems through REST API to exchange order and inventory information.

FR-6.4: Support for the ISA-95 standard for data exchange between enterprise and control layers.

3.2 Non-Functional Requirements
3.2.1 Performance
NFR-1.1: Data processing latency from the sensor to display on the dashboard must not exceed 1 second.

NFR-1.2: The system must be able to process data from at least 1000 sensors simultaneously at a rate of 1 Hz.

NFR-1.3: Response time to user requests (such as dashboard queries) must be less than 2 seconds.

NFR-1.4: The optimization algorithm must compute the optimal plan for a terminal with 50 tanks in less than 5 minutes.

3.2.2 Reliability
NFR-2.1: System availability of 99.9% 24/7 (except for planned maintenance times).

NFR-2.2: Mean time between failures (MTBF) of IoT hardware of at least 5 years.

NFR-2.3: The system must have redundancy at the server and gateway level.

NFR-2.4: Data recovery after failure (RPO) of less than 5 minutes and recovery time (RTO) of less than 30 minutes.

3.2.3 Security
NFR-3.1: Implementation of role-based access control (RBAC) and multi-factor authentication (MFA) for users.

NFR-3.2: Encryption of sensitive data at rest (AES-256) and in transit (TLS 1.3).

NFR-3.3: Compliance with the IEC 62443 standard for industrial system cybersecurity, including network segmentation, intrusion detection system (IDS) and patch management.

NFR-3.4: Complete audit log of all user activities and configuration changes.

3.2.4 Maintainability
NFR-4.1: Microservice-oriented architecture to allow independent updates of modules.

NFR-4.2: Providing system health monitoring tools (Health Check) and automatic troubleshooting.

NFR-4.3: Complete API documentation and admin guide.

3.2.5 Portability
NFR-5.1: Support for deployment on cloud environments (AWS, Azure, GCP) and on-premise (VMware, Hyper-V virtual servers).

NFR-5.2: Compatibility with major browsers (Chrome, Firefox, Edge) and mobile devices (iOS, Android).

3.2.6 Scalability
NFR-6.1: The system must scale horizontally so that it can support 10 times the initial number of sensors and tanks without performance degradation.

NFR-6.2: The time-series database must have distribution capability (such as Apache Cassandra) for storing several years of data.

3.2.7 Standards Compliance
NFR-7.1: All hardware installed in hazardous areas must have ATEX/IECEx Zone 1/2 certification.

NFR-7.2: The system must comply with API RP 2350 requirements for tank overfill protection (Overfill Protection).

NFR-7.3: The system must meet the IEC 61511 requirements for safety instrumented systems (SIS) in the parts related to emergency shutdown.

4. External Interface Requirements
4.1 User Interface
UI-1: The main dashboard must include a terminal map showing the position of tanks and their color status.

UI-2: Pages must be responsive and usable on Full HD displays.

UI-3: Support for Persian and English languages.

UI-4: The user interface must have a dark mode for low-light control room environments.

4.2 Hardware Interface
HW-1: IoT gateways must support LoRaWAN, WirelessHART and industrial Wi-Fi wireless protocols.

HW-2: Sensors must have digital output with the Modbus RTU/TCP or HART protocol.

HW-3: The system must support safety PLCs (Safety PLC) for executing emergency shutdown (ESD) functions.

4.3 Software Interface
SW-1: Providing a complete RESTful API for all functions with OpenAPI 3.0 documentation.

SW-2: Support for an OPC-UA Server to provide data to external systems.

SW-3: Connection to external SQL and NoSQL databases for data exchange.

4.4 Communication Interface
COM-1: Use of MQTT with Quality of Service (QoS) level 2 for transmitting sensor data.

COM-2: Support for the OPC-UA Pub/Sub protocol for real-time communication between modules.

COM-3: Secure VPN/IPsec connection for remote access.

5. Appendices
5.1 Synthetic Data Generation Code
To train machine learning models and test the system, a large amount of realistic synthetic data is needed. The following Python code simulates the generation of tank sensor data taking into account normal patterns and leak conditions. This code can be used to generate millions of records.

python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_tank_data(num_tanks=10, num_days=30, sampling_rate_hz=1.0,
                                 leak_probability=0.001, seed=42):
    """
    Generate synthetic data for petrochemical tanks including physical parameters and a leak indicator.
    
    Parameters:
        num_tanks: number of tanks
        num_days: number of simulation days
        sampling_rate_hz: sampling rate (Hz)
        leak_probability: probability of a leak occurring in each sample (for injecting rare events)
        seed: random seed for reproducibility
    Output:
        DataFrame with columns: timestamp, tank_id, level, temperature, pressure, density,
        flammable_gas_ppm, h2s_ppm, vibration_mm_s, corrosion_rate_mm_year, leak_event
    """
    np.random.seed(seed)
    start_time = datetime.now() - timedelta(days=num_days)
    total_samples = int(num_days * 24 * 3600 * sampling_rate_hz)
    timestamps = pd.date_range(start=start_time, periods=total_samples, freq=f'{1/sampling_rate_hz}S')
    
    data_list = []
    for tank_id in range(1, num_tanks+1):
        # Base tank parameters
        base_level = np.random.uniform(20, 80)  # initial level percentage
        base_temp = np.random.uniform(20, 35)   # degrees Celsius
        base_pressure = np.random.uniform(1.0, 2.5)  # bar
        base_density = np.random.uniform(0.7, 0.9)   # kilograms per liter
        base_flammable = np.random.uniform(5, 20)    # ppm
        base_h2s = np.random.uniform(0.1, 1.0)       # ppm
        base_vibration = np.random.uniform(0.5, 2.0) # mm/s
        base_corrosion = np.random.uniform(0.01, 0.05) # mm/year
        
        # Generate the time series with noise and trend
        level = base_level + 5*np.sin(np.linspace(0, 4*np.pi, total_samples)) + np.random.normal(0, 0.2, total_samples)
        temperature = base_temp + 3*np.sin(np.linspace(0, 2*np.pi, total_samples)) + np.random.normal(0, 0.5, total_samples)
        pressure = base_pressure + 0.1*np.cos(np.linspace(0, 6*np.pi, total_samples)) + np.random.normal(0, 0.02, total_samples)
        density = base_density + 0.01*np.sin(np.linspace(0, 8*np.pi, total_samples)) + np.random.normal(0, 0.005, total_samples)
        flammable_gas = base_flammable + 2*np.random.normal(0, 1, total_samples)
        h2s = base_h2s + 0.1*np.random.normal(0, 0.2, total_samples)
        vibration = base_vibration + 0.2*np.random.normal(0, 0.5, total_samples)
        corrosion = base_corrosion + 0.005*np.random.normal(0, 0.01, total_samples)
        
        # Clip values to the realistic range
        level = np.clip(level, 0, 100)
        temperature = np.clip(temperature, -10, 60)
        pressure = np.clip(pressure, 0.5, 5.0)
        density = np.clip(density, 0.5, 1.2)
        flammable_gas = np.clip(flammable_gas, 0, 100)
        h2s = np.clip(h2s, 0, 10)
        vibration = np.clip(vibration, 0, 10)
        corrosion = np.clip(corrosion, 0, 0.5)
        
        # Inject leak events
        leak_event = np.zeros(total_samples, dtype=int)
        # Leak pattern: sudden increase in flammable gas, pressure drop, increased vibration
        for i in range(total_samples):
            if np.random.rand() < leak_probability:
                # Leak start
                leak_duration = np.random.randint(60, 300)  # 1 to 5 minutes
                end_idx = min(i + leak_duration, total_samples)
                leak_event[i:end_idx] = 1
                # Parameter changes during the leak
                flammable_gas[i:end_idx] += np.linspace(0, 50, end_idx-i) + np.random.normal(0, 2, end_idx-i)
                h2s[i:end_idx] += np.linspace(0, 5, end_idx-i) + np.random.normal(0, 0.5, end_idx-i)
                pressure[i:end_idx] -= np.linspace(0, 0.3, end_idx-i) + np.random.normal(0, 0.01, end_idx-i)
                vibration[i:end_idx] += np.linspace(0, 3, end_idx-i) + np.random.normal(0, 0.3, end_idx-i)
                level[i:end_idx] -= np.linspace(0, 0.5, end_idx-i)  # slight level drop
                i = end_idx  # prevent overlap
                
        # Build the DataFrame for this tank
        tank_df = pd.DataFrame({
            'timestamp': timestamps,
            'tank_id': tank_id,
            'level': level,
            'temperature': temperature,
            'pressure': pressure,
            'density': density,
            'flammable_gas_ppm': flammable_gas,
            'h2s_ppm': h2s,
            'vibration_mm_s': vibration,
            'corrosion_rate_mm_year': corrosion,
            'leak_event': leak_event
        })
        data_list.append(tank_df)
    
    full_data = pd.concat(data_list, ignore_index=True)
    full_data.sort_values('timestamp', inplace=True)
    return full_data

# Usage example
if __name__ == "__main__":
    # Generate data for 10 tanks for 7 days at 1 Hz
    df = generate_synthetic_tank_data(num_tanks=10, num_days=7, sampling_rate_hz=1.0, 
                                      leak_probability=0.0005, seed=123)
    print(f"Number of generated records: {len(df)}")
    print(df.head())
    # Save to a CSV file for model training
    df.to_csv('synthetic_tank_data.csv', index=False)
Note: This code generates data with realistic distributions that include rare leak events. By adjusting leak_probability, the class ratio can be controlled. To generate large volumes (e.g., 1 million records), the number of days or tanks can be increased. Synthetic data should be combined with real data (if available) so ML models achieve high accuracy.

5.2 International Benchmarks
To ensure the completeness of the requirements, the system was compared with similar international examples. The following were added:

Digital Twin management: Based on the ISO 23247 standard (Digital Twin framework for manufacturing), the system must create a live digital model of tanks and pipelines that enables simulation and behavior prediction. (Added to FR-2.7: The system must create a digital twin for each tank that is updated with real-time data and has the ability to run What-If scenarios.)

Integration with the energy management system (ISO 50001): The optimization of loading/unloading operations must also consider energy consumption. (Added to FR-3.6: The optimization algorithm must minimize a cost function that includes pump energy consumption.)

Reliability analysis (RCM): Based on ISO 14224, the system must collect and analyze equipment failure data for reliability-centered maintenance planning. (Added to FR-1.6: The system must store equipment health data (vibration, temperature, operating hours) to calculate RCM indicators.)

Advanced cybersecurity (IEC 62443-4-2): Component-level security requirements such as secure boot, key encryption, and data flow control between zones were added. (To NFR-3.5: Hardware components must have a secure chip (TPM) for storing keys and digital signatures.)

Alarm management based on ISA-18.2 (Alarm Management): To reduce operator fatigue, the system must limit the alarm rate to a maximum of 6 alarms per hour per operator. (Added to FR-4.6: The system must implement alarm Rationalization algorithms based on ISA-18.2.)

5G communication support: For large terminals with high bandwidth, support for a private 5G network to transmit sensor data. (Added to COM-4: Gateways must be able to connect to a private 5G network.)
