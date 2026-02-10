# Sustainability

[Sustainability](https://cloud.google.com/architecture/framework/sustainability) focuses on minimizing the environmental impact of your cloud workloads.

## Core Principles

1.  **[Use Low-Carbon Regions](https://cloud.google.com/architecture/framework/sustainability/low-carbon-regions)**:
    - **Carbon Free Energy (CFE%)**: Choose regions with high CFE scores (e.g., typically >90%).
    - **Grid Intensity**: Consider the carbon intensity of the local grid.
    - **Region Picker**: Use the "Low CO2" leaf icon in Google Cloud Console.

2.  **[Optimize resource usage](https://cloud.google.com/architecture/framework/sustainability/optimize-resource-usage)**:
    - **Utilization**: Maximize resource utilization. Idle resources waste energy.
    - **Batch Jobs**: Schedule non-urgent batch jobs to run when CFE is high or in cleaner regions.
    - **Spot VMs**: Use spare capacity to increase overall cloud efficiency.

3.  **[Develop Energy-Efficient Software](https://cloud.google.com/architecture/framework/sustainability/energy-efficient-software)**:
    - **Algorithmic Efficiency**: Better code = less compute = less energy.
    - **Language Choice**: Compiled languages (Rust, C++, Go) are generally more energy-efficient than interpreted ones (Python, Ruby).
    - **Lazy Evaluation**: Don't compute what you don't need.

4.  **[Optimize Data and Storage](https://cloud.google.com/architecture/framework/sustainability/optimize-storage)**:
    - **Data Movement**: minimizing network transfer saves energy. Process data in the region where it resides.
- **Storage Lifecycle**: Delete unnecessary data. Move cold data to Archive storage (tape is very efficient).
    - **Data Format**: Use efficient formats like Parquet/Avro (columnar, compressed) instead of CSV/JSON.

5.  **[Continuously Measure](https://cloud.google.com/architecture/framework/sustainability/continuously-measure-improve)**:
    - **Carbon Footprint Dashboard**: Track gross emissions per project/service.
    - **Export Data**: Export carbon data to BigQuery for custom analysis and visualization.

## Design Review Checklist

- [ ] Is the workload running in a Low-CO2 region?
- [ ] Are idle environments (dev/test) shut down automatically?
- [ ] Are batch jobs scheduled for optimal times?
- [ ] Is data retention policy defined to delete unused data?
- [ ] Are efficient file formats (Parquet) used for analytics?
