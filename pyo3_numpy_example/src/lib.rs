use pyo3::prelude::*;
use pyo3::types::PyModule;
use numpy::ndarray::{ArrayD, ArrayViewD};
use numpy::{PyReadonlyArrayDyn, IntoPyArray, PyArrayDyn};

fn xpy(x: ArrayViewD<'_, i32>, y: ArrayViewD<'_, i32>) -> ArrayD<i32> {
    &x + &y
}

#[pyfunction]
fn add_arrays<'py>(
    py: Python<'py>,
    arr1: PyReadonlyArrayDyn<'py, i32>,
    arr2: PyReadonlyArrayDyn<'py, i32>,
) -> Bound<'py, PyArrayDyn<i32>> {
    let x = arr1.as_array();
    let y = arr2.as_array();
    let z = xpy(x, y);
    z.into_pyarray(py)
}

#[pymodule]
//fn rust_array_ext<'py>(_py: Python<'py>, m: &Bound<'_, PyModule>) -> PyResult<()> {
fn rust_array_ext(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add_arrays, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_arrays() {
        let arr1 = Array::from_vec(vec![1, 2, 3, 4]).into_dyn();
        let arr2 = Array::from_vec(vec![5, 6, 7, 8]).into_dyn();
        let res = arr1 + arr2;
        assert_eq!(result.into_raw_vec(), vec![6, 8, 10, 12]);
    }
}
