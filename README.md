# ParaSuit

Enhancing Usability and Performance of Symbolic Execution via Fully Automated Parameter Tuning

<img src="https://github.com/anonymousfse2024/parasuit/assets/150991397/d405595c-1eb7-4cd9-a100-f30450bf3bb4" width=30%, height=30%/>



## Parameter Selection 
At this stage, ParaSuit selects parameters that are deemed worthy of tuning among the many parameters that exist in the Symbolic Executor. Using the parameters selected in this stage, the values ​​of the corresponding parameters are defined in subsequent stage.

You can see detailed process in "paramselect.py" file.
  
    

## Parameter Space Construction
This stage aims to automatically construct the parameter space for each parameter selected in Parameter Selection stage. In this stage, ParaSuit selects random values ​​for each parameter and tries as many different values ​​as possible for the parameter value. Once enough amount of data has been accumulated, ParaSuit limits the space of sampling and moves to the Parameter Value Sampling stage using previously used values.

You can see detailed process in "psconstruct.py" file.



## Parameter Value Sampling
In this stage, ParaSuit takes data of parameter spaces from Paramete Space Construction stage. ParaSuit samples parameter values based on different sampling probabilities in the parameter spaces. After sampling parameter values, ParaSuit sends the values to Symbolic Exetuion tool(e.g. KLEE). 

You can see detailed process in "pvsample.py" file.




KLEE finally runs symbolic execution using parameter values from ParaSuit, and then outputs covered branches as a result. And ParaSuit uses the output to tune parameter values ​​for the next iteration. 

We set the time budget(= iteration time budget) to 120 seconds and execute the Symbolic Executor repeatedly, with one execution defined as "iteration". ParaSuit repeats iteration until the experiment time budget expires.
