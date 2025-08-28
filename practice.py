class Temperature:
    def __init__(self, celsius):
        # We store the temperature in Celsius in a "private" attribute
        self._celsius = celsius

    @property
    def celsius(self):
        """The getter for the celsius attribute."""
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        """The setter for the celsius attribute, with validation."""
        if value < -273.15:  # Absolute zero
            raise ValueError("Temperature cannot be below absolute zero.")
        self._celsius = value

    @property
    def fahrenheit(self):
        """A getter that calculates the value on the fly."""
        return (self.celsius * 9/5) + 32

# Create an instance
t = Temperature(20)

# Accessing attributes
print(f"Initial Celsius: {t.celsius}°C")
print(f"Initial Fahrenheit: {t.fahrenheit}°F")

# Setting a new value
t.celsius = 30
print(f"New Celsius: {t.celsius}°C")
print(f"New Fahrenheit: {t.fahrenheit}°F")

# The setter method's validation runs automatically
try:
    t.celsius = -300
except ValueError as e:
    print(f"Error: {e}")