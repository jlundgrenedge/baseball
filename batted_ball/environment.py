"""
Environmental factors affecting baseball flight.

This module calculates air density and other environmental effects based on:
- Altitude (elevation above sea level)
- Temperature
- Humidity
- Atmospheric pressure
"""

import math
from .constants import (
    RHO_SEA_LEVEL,
    TEMP_REFERENCE_K,
    PRESSURE_SEA_LEVEL,
    LAPSE_RATE,
    FEET_TO_METERS,
)


class Environment:
    """
    Represents environmental conditions for a baseball game.

    Calculates air density based on altitude, temperature, and humidity,
    which significantly affects ball flight through drag and Magnus forces.
    """

    def __init__(
        self,
        altitude_ft=0.0,
        temperature_f=70.0,
        relative_humidity=0.5,
        pressure_pa=None
    ):
        """
        Initialize environment with given conditions.

        Parameters
        ----------
        altitude_ft : float
            Elevation above sea level in feet (default: 0 = sea level)
        temperature_f : float
            Temperature in Fahrenheit (default: 70°F)
        relative_humidity : float
            Relative humidity as fraction 0-1 (default: 0.5 = 50%)
        pressure_pa : float, optional
            Atmospheric pressure in Pascals. If None, calculated from altitude.
        """
        self.altitude_ft = altitude_ft
        self.altitude_m = altitude_ft * FEET_TO_METERS
        self.temperature_f = temperature_f
        self.temperature_c = (temperature_f - 32.0) * 5.0 / 9.0
        self.temperature_k = self.temperature_c + 273.15
        self.relative_humidity = relative_humidity

        # Calculate or use provided pressure
        if pressure_pa is None:
            self.pressure = self._calculate_pressure()
        else:
            self.pressure = pressure_pa

        # Calculate air density
        self.air_density = self._calculate_air_density()

    def _calculate_pressure(self):
        """
        Calculate atmospheric pressure at given altitude.

        Uses barometric formula for standard atmosphere.

        Returns
        -------
        float
            Atmospheric pressure in Pascals
        """
        # Barometric formula: P = P0 * (1 - L*h/T0)^(g*M/(R*L))
        # Simplified version for typical baseball altitudes

        # Standard atmosphere approximation
        # Pressure decreases roughly exponentially with altitude
        exponent = -self.altitude_m / 8400.0  # 8400m is scale height
        pressure = PRESSURE_SEA_LEVEL * math.exp(exponent)

        return pressure

    def _calculate_air_density(self):
        """
        Calculate air density considering temperature, pressure, and humidity.

        Uses ideal gas law with corrections for water vapor.

        Returns
        -------
        float
            Air density in kg/m³
        """
        # Gas constant for dry air
        R_dry = 287.05  # J/(kg·K)

        # Calculate saturation vapor pressure (Magnus formula)
        e_sat = 611.2 * math.exp(
            17.67 * self.temperature_c / (self.temperature_c + 243.5)
        )

        # Actual vapor pressure
        e_actual = self.relative_humidity * e_sat

        # Partial pressure of dry air
        p_dry = self.pressure - e_actual

        # Air density from ideal gas law (with humidity correction)
        # Humid air is less dense than dry air
        rho_dry = p_dry / (R_dry * self.temperature_k)

        # Water vapor density (if needed for more accuracy)
        R_vapor = 461.5  # J/(kg·K)
        rho_vapor = e_actual / (R_vapor * self.temperature_k)

        # Total air density
        rho = rho_dry + rho_vapor

        return rho

    def get_density_ratio(self):
        """
        Get air density relative to sea level standard conditions.

        Returns
        -------
        float
            Ratio of current air density to sea level density
            (values < 1 mean thinner air, > 1 mean denser air)
        """
        return self.air_density / RHO_SEA_LEVEL

    def get_altitude_effect_feet(self):
        """
        Estimate additional carry distance due to altitude alone.

        Based on empirical rule: ~6 feet per 1000 feet altitude

        Returns
        -------
        float
            Additional distance in feet (positive = more carry)
        """
        return (self.altitude_ft / 1000.0) * 6.0

    def get_temperature_effect_feet(self, reference_temp_f=70.0):
        """
        Estimate additional carry distance due to temperature.

        Based on empirical rule: ~0.35 feet per degree F above reference

        Parameters
        ----------
        reference_temp_f : float
            Reference temperature in Fahrenheit (default: 70°F)

        Returns
        -------
        float
            Additional distance in feet (positive = more carry)
        """
        temp_diff = self.temperature_f - reference_temp_f
        return temp_diff * 0.35

    def __repr__(self):
        return (
            f"Environment(altitude={self.altitude_ft:.0f} ft, "
            f"temp={self.temperature_f:.1f}°F, "
            f"humidity={self.relative_humidity*100:.0f}%, "
            f"air_density={self.air_density:.4f} kg/m³)"
        )


def create_standard_environment():
    """
    Create environment with standard sea level conditions.

    Returns
    -------
    Environment
        Standard conditions: sea level, 70°F, 50% humidity
    """
    return Environment(
        altitude_ft=0.0,
        temperature_f=70.0,
        relative_humidity=0.5
    )


def create_coors_field_environment(temperature_f=70.0):
    """
    Create environment for Coors Field in Denver, CO.

    Coors Field is famous for home runs due to high altitude (5,200 ft).

    Parameters
    ----------
    temperature_f : float
        Temperature in Fahrenheit (default: 70°F)

    Returns
    -------
    Environment
        Coors Field conditions at given temperature
    """
    return Environment(
        altitude_ft=5200.0,
        temperature_f=temperature_f,
        relative_humidity=0.3  # Denver is typically dry
    )


def create_fenway_park_environment(temperature_f=70.0):
    """
    Create environment for Fenway Park in Boston, MA.

    Parameters
    ----------
    temperature_f : float
        Temperature in Fahrenheit (default: 70°F)

    Returns
    -------
    Environment
        Fenway Park conditions (approximately sea level)
    """
    return Environment(
        altitude_ft=20.0,  # Boston is approximately at sea level
        temperature_f=temperature_f,
        relative_humidity=0.6  # Coastal humidity
    )


# Convenience function for quick air density calculation
def calculate_air_density(altitude_ft=0.0, temperature_f=70.0, humidity=0.5):
    """
    Quick calculation of air density.

    Parameters
    ----------
    altitude_ft : float
        Altitude in feet
    temperature_f : float
        Temperature in Fahrenheit
    humidity : float
        Relative humidity (0-1)

    Returns
    -------
    float
        Air density in kg/m³
    """
    env = Environment(altitude_ft, temperature_f, humidity)
    return env.air_density
