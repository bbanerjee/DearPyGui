#[unsafe(no_mangle)]
pub extern "C" fn fib_rs(n: i32) -> i32 {
    if n <= 0 {
        0
    } else if n == 1 {
        1
    } else {
        let mut a: i32 = 0;
        let mut b: i32 = 1;
        for _ in 0..(n-1) {
            let temp = a;
            a = b;
            b = temp + b;
        }
        b
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fib_rs() {
        assert_eq!(fib_rs(0), 0);
        assert_eq!(fib_rs(1), 1);
        assert_eq!(fib_rs(2), 1);
        assert_eq!(fib_rs(3), 2);
        assert_eq!(fib_rs(10), 55);
    }
}
