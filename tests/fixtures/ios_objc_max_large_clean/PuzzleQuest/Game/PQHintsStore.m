#import "PQHintsStore.h"

static NSString *const kKey = @"puzzlequest.hints";

@implementation PQHintsStore

+ (instancetype)sharedStore
{
    static PQHintsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQHintsStore alloc] init];
    });
    return shared;
}

- (NSInteger)remaining
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setRemaining:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
