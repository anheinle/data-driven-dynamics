/*
 * Copyright 2017 Pavel Vechersky, ASL, ETH Zurich, Switzerland
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0

 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef PARAMETRIC_DYNAMICS_MODEL_H
#define PARAMETRIC_DYNAMICS_MODEL_H

#include "aero_parameters.h"

#include <Eigen/Eigen>
#include <ignition/math.hh>

// Constants.
static constexpr double kAirDensity = 1.18;
static constexpr double kGravity = 9.81;
static constexpr double kMinAirSpeedThresh = 0.1;

namespace gazebo {

class ParametricDynamicsModel {
 public:
  ParametricDynamicsModel();
  virtual ~ParametricDynamicsModel();
  void setState(const ignition::math::Vector3d &B_air_speed_W_B, const ignition::math::Vector3d &B_angular_velocity_W_B,
                const Eigen::VectorXd actuator_inputs);
  void LoadAeroParams(std::string aero_params_yaml) { aero_params_->LoadAeroParamsYAML(aero_params_yaml); };
  Eigen::Vector3d getForce() { return force_; };
  Eigen::Vector3d getMoment() { return moment_; };
  std::shared_ptr<FWAerodynamicParameters> getAeroParams() { return aero_params_; };
  inline static Eigen::Vector3d ignition2eigen(const ignition::math::Vector3d &vec) {
    return Eigen::Vector3d(vec.X(), vec.Y(), vec.Z());
  };

 private:
  void computeTotalRotorWrench(const Eigen::Vector3d airspeed, const Eigen::VectorXd &actuator_inputs,
                               Eigen::Vector3d &rotor_force, Eigen::Vector3d &rotor_moment);
  Eigen::Vector3d computeRotorForce(const Eigen::Vector3d airspeed, const double actuator_input,
                                    const RotorParameters &rotor_params);
  Eigen::Vector3d computeRotorMoment(const Eigen::Vector3d airspeed, const double actuator_input,
                                     const RotorParameters &rotor_params, Eigen::Vector3d rotor_force);
  Eigen::Vector3d force_{Eigen::Vector3d::Zero()};
  Eigen::Vector3d moment_{Eigen::Vector3d::Zero()};
  /// \brief    Throttle input, in range from 0 to 1.
  double throttle_{0.0};
  /// \brief    The aerodynamic properties of the aircraft.
  std::shared_ptr<FWAerodynamicParameters> aero_params_;
};
}  // namespace gazebo
#endif  // PARAMETRIC_DYNAMICS_MODEL_H
