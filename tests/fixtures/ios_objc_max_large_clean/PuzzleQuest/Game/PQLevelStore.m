#import "PQLevelStore.h"

static NSString *const kKey = @"puzzlequest.level";

@implementation PQLevelStore

+ (instancetype)sharedStore
{
    static PQLevelStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQLevelStore alloc] init];
    });
    return shared;
}

- (NSInteger)current
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCurrent:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
