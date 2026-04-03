import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create figure and axis
fig, ax = plt.subplots(figsize=(12, 8))

# Define box positions and dimensions
box_props = {
    "facecolor": "lightblue",
    "edgecolor": "black",
    "boxstyle": "round,pad=0.3"
}
arrow_props = {"arrowstyle": "->", "color": "black"}

# Add prediction step box
ax.text(0.1, 0.8, "Prediction Step\nState: f(x, u)\nCovariance: P'",
        fontsize=10, ha="center", bbox=box_props)

# Add update step box
ax.text(0.7, 0.8, "Update Step\nMeasurement: z\nState: x'\nCovariance: P",
        fontsize=10, ha="center", bbox=box_props)

# Add process model box
ax.text(0.1, 0.6, "State Transition Model\nf(x, u)", fontsize=10, ha="center", bbox=box_props)

# Add measurement model box
ax.text(0.7, 0.6, "Measurement Model\nh(x)", fontsize=10, ha="center", bbox=box_props)

# Add state estimation box
ax.text(0.4, 0.4, "State Estimation\nKalman Gain K", fontsize=10, ha="center", bbox=box_props)

# Draw arrows between boxes
ax.annotate("", xy=(0.1, 0.75), xytext=(0.1, 0.65), arrowprops=arrow_props)  # Prediction to process model
ax.annotate("", xy=(0.7, 0.75), xytext=(0.7, 0.65), arrowprops=arrow_props)  # Update to measurement model
ax.annotate("", xy=(0.1, 0.65), xytext=(0.4, 0.45), arrowprops=arrow_props)  # Process model to state estimation
ax.annotate("", xy=(0.7, 0.65), xytext=(0.4, 0.45), arrowprops=arrow_props)  # Measurement model to state estimation
ax.annotate("", xy=(0.4, 0.35), xytext=(0.1, 0.25), arrowprops=arrow_props)  # State estimation to prediction loop
ax.annotate("", xy=(0.4, 0.35), xytext=(0.7, 0.25), arrowprops=arrow_props)  # State estimation to update loop

# Add feedback loop label
ax.text(0.4, 0.2, "Iterative Refinement", fontsize=10, ha="center")

# Remove axes for a clean look
ax.axis("off")

# Display the figure
plt.title("Extended Kalman Filter (EKF) Principle Diagram", fontsize=14)
plt.show()
