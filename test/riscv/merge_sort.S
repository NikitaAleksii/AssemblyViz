.data
array:    .word   24, 10, 35, 2, 3, 0, 353
length:   .word   7
space:    .asciz  " "
newline:  .asciz  "\n"

.text
main:
  la    a0, array # a0 = arr base

  li    a1, 0 # a1 = left

  la    a2, length # a2 = right
  lw    a2, 0(a2)
  addi  a2, a2, -1

  jal   ra, merge_sort

  la    s0, array # s0 = base address
  la    t0, length
  lw    s1, 0(t0)# s1 = length

  li    t0, 0 # i = 0

print_loop:
  bge   t0, s1, done_print

  slli  t1, t0, 2
  add   t2, s0, t1
  lw    a0, 0(t2)# load arr[i]

  li    a7, 1
  ecall # print integer

  la    a0, space
  li    a7, 4
  ecall # print space

  addi  t0, t0, 1
  j     print_loop

done_print:
  la    a0, newline
  li    a7, 4
  ecall

  li    a7, 10 # exit
  ecall

merge:
  addi  sp, sp, -16
  sw    ra, 12(sp)
  sw    s0, 8(sp)
  sw    s1, 4(sp)
  sw    s7, 0(sp)

# n1 = mid - left + 1
  addi  t3, a3, 1
  sub   t3, t3, a1 # t3 = n1

# n2 = right - mid
  sub   t4, a2, a3 # t4 = n2

# bytes for left temp and right temp
  slli  t5, t3, 2 # t5 = n1 * 4
  slli  t6, t4, 2 # t6 = n2 * 4

# after calculating t5 = n1*4, t6 = n2*4
  add   t0, t5, t6 # total_bytes = (n1+n2)*4

# Round UP to next multiple of 16
  addi  t0, t0, 15
  andi  t0, t0, -16 # t0 = ceil(total_bytes / 16) * 16

  sub   sp, sp, t0
  mv    s7, t0 # s7 = total bytes; save bytes on stack

# temp left base
  mv    s0, sp # s0 = left temp base
# temp right base
  add   s1, sp, t5 # s1 = right temp base

  li    t0, 0 # t0 = i

loop_left:
  bge   t0, t3, loop_left_done

  add   t1, a1, t0 # t1 = left + i
  slli  t1, t1, 2  # t1 = (left+i)*4
  add   t1, a0, t1 # t1 = &arr[left+i]
  lw    t2, 0(t1)  # t2 = arr[left+i]

  slli  t1, t0, 2 # t1 = i*4
  add   t1, s0, t1 # t1 = &leftTemp[i]
  sw    t2, 0(t1) # leftTemp[i] = arr[left+i]

  addi  t0, t0, 1
  j     loop_left

loop_left_done:
  li    t0, 0 # t0 = j

loop_right:
  bge   t0, t4, loop_right_done

  add   t1, a3, t0 # t1 = mid + j
  addi  t1, t1, 1 # t1 = mid + j + 1
  slli  t1, t1, 2 # t1 = (mid+j+1)*4
  add   t1, a0, t1 # t1 = &arr[mid+j+1]
  lw    t2, 0(t1) # t2 = arr[mid+j+1]

  slli  t1, t0, 2 # t1 = j*4
  add   t1, s1, t1 # t1 = &rightTemp[j]
  sw    t2, 0(t1) # rightTemp[j] = arr[mid+j+1]

  addi  t0, t0, 1
  j     loop_right
loop_right_done:

  li    t0, 0  # t0 = i
  li    t1, 0  # t1 = j
  mv    t2, a1 # t2 = k

merge_loop:
  bge   t0, t3, merge_done # if i >= n1 break
  bge   t1, t4, merge_done # if j >= n2 break

# leftVal = leftTemp[i]
  slli  a4, t0, 2
  add   a4, s0, a4
  lw    a4, 0(a4)

# rightVal = rightTemp[j]
  slli  a5, t1, 2
  add   a5, s1, a5
  lw    a5, 0(a5)

# if rightVal < leftVal -> take right
  blt   a5, a4, take_right

take_left:
  slli  t5, t2, 2
  add   t5, a0, t5
  sw    a4, 0(t5)
  addi  t0, t0, 1 # i++
  addi  t2, t2, 1 # k++
  j     merge_loop

take_right:
  slli  t5, t2, 2
  add   t5, a0, t5
  sw    a5, 0(t5)
  addi  t1, t1, 1 # j++
  addi  t2, t2, 1 # k++
  j     merge_loop

merge_done:
copy_left:
  bge   t0, t3, copy_right

  slli  a4, t0, 2
  add   a4, s0, a4
  lw    a4, 0(a4)

  slli  t5, t2, 2
  add   t5, a0, t5
  sw    a4, 0(t5)

  addi  t0, t0, 1 # i++
  addi  t2, t2, 1 # k++
  j     copy_left

copy_right:
  bge   t1, t4, done

  slli  a5, t1, 2
  add   a5, s1, a5
  lw    a5, 0(a5)

  slli  t5, t2, 2
  add   t5, a0, t5
  sw    a5, 0(t5)

  addi  t1, t1, 1 # j++
  addi  t2, t2, 1 # k++
  j     copy_right

done:
  add   sp, sp, s7 # free temp arrays

  lw    s7, 0(sp)
  lw    s1, 4(sp)
  lw    s0, 8(sp)
  lw    ra, 12(sp)
  addi  sp, sp, 16
  ret

merge_sort:
  bge   a1, a2, ms_ret # if left >= right return

  sub   t1, a2, a1 # t1 = right - left
  srli  t1, t1, 1  # t1 = (right-left)/2
  add   t3, a1, t1 # t3 = mid

  addi  sp, sp, -16 # stack frame
  sw    a1, 12(sp) # save left
  sw    a2, 8(sp) # save right
  sw    ra, 4(sp) # save ra
  sw    t3, 0(sp) # save mid

  mv    a2, t3
  jal   ra, merge_sort # merge_sort(left, mid)

  lw    a1, 12(sp)
  lw    a2, 8(sp)
  lw    t3, 0(sp)

  addi  a1, t3, 1
  jal   ra, merge_sort # merge_sort(mid+1, right)

  lw    a1, 12(sp)
  lw    a2, 8(sp)
  lw    t3, 0(sp)

  mv    a3, t3
  jal   ra, merge # merge(left, mid, right)

  lw    ra, 4(sp)
  addi  sp, sp, 16

  ret

ms_ret:
  ret
